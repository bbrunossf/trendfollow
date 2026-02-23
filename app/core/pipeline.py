# """
# Pipeline para executar o primeiro grafico e filtrar os ativos.

# Responsável por orquestrar:
# - scoring
# - ranking
# - preparação de payload para API / frontend
# """

from typing import Dict, Any
import pandas as pd
import numpy as np

from app.data.market_data import (
    list_b3_assets, get_asset_metadata, get_price_history, 
    download_price_history,
    normalize_price_columns,
    generate_theoretical_dates,
    get_download_window, enrich_with_metadata_and_52w_high
)

from app.data.preprocessing import (
    resolve_to_trading_dates,
    extract_price_snapshots,
    flatten_snapshot_for_scoring,
    build_price_matrix_for_chart,
    build_plotly_price_dataframe,
    add_percent_change_for_hover,
    extract_latest
)

from app.services.scoring import calculate_relative_strength
from app.services.ranking import build_ranking

from app.finance.moving_averages import simple_moving_average
from app.finance.bollinger import calculate_bollinger_bands
from app.finance.macd import calculate_macd
from app.finance.volatility import calculate_atr_and_stop

from app.finance.indicators import calculate_risk_return_indicators


import app.config as config


def run_pipeline(
    prices: pd.DataFrame,
    reference_date: str | None = None
) -> Dict[str, Any]:
    """
    Pipeline de ranking e visualização (etapas 5+).

    Assume que o histórico de preços (`prices`) já foi:
    - baixado
    - normalizado
    - enriquecido com indicadores técnicos (etapas 1–4)

    Responsabilidades:
    - resolver datas válidas
    - extrair snapshots
    - calcular força relativa
    - ranquear ativos
    - preparar payload para gráficos e tabela
    """

    
    df_latest = extract_latest(prices, price_field="Adj Close", indicator_fields=None)
    df_latest['Ticker'] = df_latest['Ticker'].astype(str).str.strip().str.upper()

    # ------------------------------------------------------------------
    # 5. Resolução das datas válidas e snapshots
    # ------------------------------------------------------------------
    theoretical_dates = generate_theoretical_dates(reference_date)
    
    trading_dates = resolve_to_trading_dates(
        prices.index,
        theoretical_dates
    )    

    price_snapshots = extract_price_snapshots(
        prices,
        trading_dates,
        price_field="Adj Close"
    )
        
    df = flatten_snapshot_for_scoring(price_snapshots) #aqui o df deixa de ser multiindex    
      

    # ------------------------------------------------------------------
    # 6. Scoring (Força Relativa)
    # ------------------------------------------------------------------
    scored = calculate_relative_strength(df)

    if scored.empty:
        return {"summary": {"message": "Nenhum ativo pontuado"},
                "ranking": [], "charts": {}}
                
    
    # ------------------------------------------------------------------
    # 7. Ranking
    # ------------------------------------------------------------------    
    #aqui o df final é desprovido de qualquer coisa inicial; só tem as colunas com os preços nas datas selecionada, o ticker e o valor de FR e FR_Rank
    ranking_result = build_ranking(
    df=scored,
    score_column="FR",
    min_score=config.MIN_FR,
    top_n=config.TOP_N,
    payload_fields=["FR", "FR_rank"]
    )
    
    if not ranking_result["payload"]:
        return {
            "summary": {"message": "Nenhum ativo passou no ranking"},
            "ranking": [],
            "charts": {}
        }
    
    # ------------------------------------------------------------------
    # 9. Pós-ranking: merge + enriquecimento + indicadores finais
    # ------------------------------------------------------------------
    df_ranked = pd.DataFrame(ranking_result["payload"])
    df_ranked["ticker"] = (
        df_ranked["ticker"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    df_latest = df_latest.rename(columns={"Ticker": "ticker"})

    df_ranked = df_ranked.merge(
        df_latest,
        on="ticker",
        how="left",
        validate="m:1"
    )

    df_enriched = enrich_with_metadata_and_52w_high(
        df=df_ranked,
        ticker_column="ticker"
    )

    df_final = calculate_risk_return_indicators(
        df=df_enriched,
        price_col="Adj Close",
        stop_col="STOP_ATR_14_1.5",
        high_52w_col="high_52w"
    )

    # ------------------------------------------------------------------
    # 10. Sanitização para JSON e montagem do payload
    # ------------------------------------------------------------------
    df_clean = df_final.copy()
    df_clean.replace([np.inf, -np.inf], np.nan, inplace=True)

    num = df_clean.select_dtypes(include=[np.number])
    bad_mask = ~np.isfinite(num)

    if bad_mask.any().any():
        bad_cols = bad_mask.any()[bad_mask.any()].index.tolist()
        print("Colunas com valores não finitos:", bad_cols)

    ranking_records = df_clean.to_dict(orient="records")

    for row in ranking_records:
        for key, value in row.items():
            if value is None:
                continue
            if isinstance(value, float) and not np.isfinite(value):
                row[key] = None

    summary = {
        "scored_assets": len(scored),
        "ranked_assets": len(ranking_records),
        "reference_date": reference_date
    }

    charts = {
        "price_snapshots": price_snapshots
    }

    return {
        "summary": summary,
        "ranking": ranking_records,
        "charts": charts
    }