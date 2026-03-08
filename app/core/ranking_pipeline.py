"""
ranking_pipeline.py

Pipeline de scoring, ranking e enriquecimento de ativos (passos 5–9).

Responsabilidades:
- resolver datas de pregão válidas a partir de datas teóricas
- extrair snapshots de preço por data
- calcular Força Relativa (scoring)
- ranquear e filtrar ativos
- enriquecer o ranking com metadados, indicadores e métricas de risco/retorno
- sanitizar e estruturar o payload final

Este módulo NÃO:
- baixa dados de mercado
- calcula indicadores técnicos no histórico completo
- monta payloads Plotly
- conhece endpoints ou detalhes de HTTP
"""

from typing import Any, Dict

import numpy as np
import pandas as pd

import app.config as config
from app.data.market_data import (
    enrich_with_metadata_and_52w_high,
    generate_theoretical_dates,
)
from app.data.preprocessing import (
    extract_latest,
    extract_price_snapshots,
    flatten_snapshot_for_scoring,
    resolve_to_trading_dates,
)
from app.finance.indicators import calculate_risk_return_indicators
from app.services.ranking import build_ranking
from app.services.scoring import calculate_relative_strength


def build_ranking_result(
    prices: pd.DataFrame,
    reference_date: str | None = None,
) -> Dict[str, Any]:
    """
    Executa os passos 5–9 do pipeline: scoring → ranking → enriquecimento.

    Assume que ``prices`` já foi:
    - baixado e normalizado (passo 1–3, responsabilidade de ``init``)
    - enriquecido com indicadores técnicos no histórico completo (passo 4)

    Parâmetros
    ----------
    prices : pd.DataFrame
        DataFrame MultiIndex (Field, Ticker) com histórico de preços e
        indicadores técnicos já calculados.
    reference_date : str | None
        Data de referência no formato YYYY-MM-DD.
        Se None, usa a data de hoje.

    Retorno
    -------
    dict com as chaves:
    - ``"summary"``         : dict com métricas resumidas da execução
    - ``"ranking"``         : list[dict] dos ativos ranqueados e enriquecidos,
                              prontos para serialização JSON
    - ``"price_snapshots"`` : pd.DataFrame MultiIndex com snapshots de preço
                              nas datas resolvidas (consumido pelo chart builder)

    Retornos antecipados (sem erro):
    - Nenhum ativo pontuado  → ranking e price_snapshots vazios
    - Nenhum ativo no ranking → ranking vazio, price_snapshots disponível
    """

    # ------------------------------------------------------------------
    # 5. Extração do último valor de indicadores por ticker
    # ------------------------------------------------------------------
    df_latest = extract_latest(prices, price_field="Adj Close", indicator_fields=None)
    df_latest["Ticker"] = df_latest["Ticker"].astype(str).str.strip().str.upper()

    # ------------------------------------------------------------------
    # 6. Resolução das datas válidas e extração de snapshots
    # ------------------------------------------------------------------
    # Garante que reference_date seja sempre uma str concreta antes de
    # repassar para generate_theoretical_dates, que não aceita None
    reference_date = reference_date or str(pd.Timestamp.today().date())

    theoretical_dates = generate_theoretical_dates(reference_date)

    trading_dates = resolve_to_trading_dates(
        prices.index,
        theoretical_dates,
    )

    price_snapshots = extract_price_snapshots(
        prices,
        trading_dates,
        price_field="Adj Close",
    )

    # flat: índice = ticker, colunas = p0..pN (preços nas datas selecionadas)
    df_flat = flatten_snapshot_for_scoring(price_snapshots)

    # ------------------------------------------------------------------
    # 7. Scoring — Força Relativa (FR)
    # ------------------------------------------------------------------
    scored = calculate_relative_strength(df_flat)

    if scored.empty:
        return {
            "summary": {"message": "Nenhum ativo pontuado"},
            "ranking": [],
            "price_snapshots": price_snapshots,
        }

    # ------------------------------------------------------------------
    # 8. Ranking — ordenação, percentil e filtro
    # ------------------------------------------------------------------
    ranking_result = build_ranking(
        df=scored,
        score_column="FR",
        min_score=config.MIN_FR,
        top_n=config.TOP_N,
        payload_fields=["FR", "FR_rank"],
    )

    if not ranking_result["payload"]:
        return {
            "summary": {"message": "Nenhum ativo passou no ranking"},
            "ranking": [],
            "price_snapshots": price_snapshots,
        }

    # ------------------------------------------------------------------
    # 9. Pós-ranking: merge com últimos valores + metadados + risco/retorno
    # ------------------------------------------------------------------
    df_ranked = pd.DataFrame(ranking_result["payload"])
    df_ranked["ticker"] = df_ranked["ticker"].astype(str).str.strip().str.upper()

    df_latest = df_latest.rename(columns={"Ticker": "ticker"})

    df_ranked = df_ranked.merge(
        df_latest,
        on="ticker",
        how="left",
        validate="m:1",
    )

    df_enriched = enrich_with_metadata_and_52w_high(
        df=df_ranked,
        ticker_column="ticker",
    )

    df_final = calculate_risk_return_indicators(
        df=df_enriched,
        price_col="Adj Close",
        stop_col="STOP_ATR_14_1.5",
        high_52w_col="high_52w",
    )
    #debug: colunas do ranking
    #print("COLUNAS DO DF DE RANKING:")
    #print(df_final.columns)
    #Index(['ticker', 'FR', 'FR_rank', 'Adj Close', 'STOP_ATR_14_1.5', 'industry',
    #   'sector', 'symbol', 'shortName', 'high_52w', 'distancia', 'Risco_%',
    #   'Retorno_Risco'],

    #teste tirando algumas colunas para tabela ficar totalmente legível
    df_final = df_final[['ticker', 'FR_rank', 'Adj Close', 'sector', 'shortName', 'high_52w', 'Retorno_Risco', 'distancia', 'Risco_%']]

    # ------------------------------------------------------------------
    # 10. Sanitização para serialização JSON
    # ------------------------------------------------------------------
    df_clean = df_final.copy()
    df_clean.replace([np.inf, -np.inf], np.nan, inplace=True)

    num_cols = df_clean.select_dtypes(include=[np.number])
    non_finite_mask = ~np.isfinite(num_cols)
    if non_finite_mask.any().any():
        bad_cols = non_finite_mask.any()[non_finite_mask.any()].index.tolist()
        print(f"[ranking_pipeline] Colunas com valores não finitos: {bad_cols}")

    ranking_records = df_clean.to_dict(orient="records")

    # Substitui float não-finitos por None (JSON-safe)
    for row in ranking_records:
        for key, value in row.items():
            if isinstance(value, float) and not np.isfinite(value):
                row[key] = None

    # ------------------------------------------------------------------
    # 11. Montagem do retorno
    # ------------------------------------------------------------------
    summary = {
        "scored_assets": len(scored),
        "ranked_assets": len(ranking_records),
        "reference_date": reference_date,
    }

    return {
        "summary": summary,
        "ranking": ranking_records,
        "price_snapshots": price_snapshots,
    }
