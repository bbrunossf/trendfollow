"""
routes.py

Camada de transporte HTTP da aplicação.

Responsabilidades:
- receber requisições HTTP e validar parâmetros de entrada
- orquestrar chamadas aos repositórios e builders (sem lógica de negócio inline)
- serializar e retornar respostas JSON

Este módulo NÃO:
- calcula indicadores técnicos
- executa scoring ou ranking
- monta payloads Plotly diretamente
"""

from datetime import date
from typing import Optional

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from app.charts.chart_builders import (
    build_candle_chart_payload,
    build_fr_chart_payload,
    build_scatter_chart_payload,
)
from app.core.init import init
from app.core.price_repository import price_repository
from app.core.ranking_pipeline import build_ranking_result
from app.core.ranking_repository import ranking_repository

router = APIRouter()


# ===========================================================================
# /api/fr-price-series
# Gráfico 1 — Força Relativa + tabela de ranking
# ===========================================================================


@router.get("/fr-price-series")
def get_fr_price_series(
    reference_date: Optional[str] = Query(
        default=None,
        description="Data de referência no formato YYYY-MM-DD",
    ),
):
    """
    Endpoint principal acionado ao clicar em "Run".

    Garante que o histórico de preços e o resultado do ranking estejam
    calculados e cacheados. Retorna o payload completo para:
    - Gráfico 1 (Força Relativa) via Plotly
    - Tabela de ranking (embutida na resposta, sem chamada adicional ao backend)

    Retorno
    -------
    {
        "data"    : list[dict]  — traces Plotly para o gráfico de FR
        "layout"  : dict        — layout Plotly
        "ranking" : list[dict]  — ativos ranqueados prontos para a tabela
    }
    """

    # Garante que reference_date seja sempre uma str concreta
    reference_date = reference_date or str(date.today())

    # ------------------------------------------------------------------
    # 1. Garante histórico de preços com indicadores (passos 1–4)
    # ------------------------------------------------------------------
    if not price_repository.has(reference_date):
        prices = init(reference_date)
        price_repository.set(reference_date, prices)

    prices = price_repository.get(reference_date)

    # ------------------------------------------------------------------
    # 2. Garante resultado do pipeline de ranking (passos 5–9)
    #    build_ranking_result é executado uma única vez por reference_date
    # ------------------------------------------------------------------
    if not ranking_repository.has(reference_date):
        result = build_ranking_result(prices=prices, reference_date=reference_date)
        ranking_repository.set(reference_date, result)

    result = ranking_repository.get(reference_date)

    ranking = result.get("ranking", [])
    price_snapshots: pd.DataFrame = result["price_snapshots"]

    if not ranking:
        raise HTTPException(
            status_code=404,
            detail="Nenhum ativo passou pelo ranking para a data de referência informada.",
        )

    # ------------------------------------------------------------------
    # 3. Monta payload Plotly para o gráfico de FR
    # ------------------------------------------------------------------
    try:
        chart_payload = build_fr_chart_payload(
            price_snapshots=price_snapshots,
            ranking=ranking,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # ------------------------------------------------------------------
    # 4. Retorna gráfico + ranking em uma única resposta
    #    O frontend (fr_chart.js) usa result.ranking diretamente,
    #    eliminando a necessidade de chamar /api/ranking separadamente.
    # ------------------------------------------------------------------
    return {
        "data": chart_payload["data"],
        "layout": chart_payload["layout"],
        "ranking": ranking,
    }


# ===========================================================================
# /api/ranking
# Leitura do ranking cacheado (sem recomputação)
# ===========================================================================


@router.get("/ranking")
def get_ranking():
    """
    Retorna o ranking cacheado da última execução.

    Não reexecuta o pipeline — apenas lê o resultado já armazenado
    no RankingRepository pelo endpoint /api/fr-price-series.

    Útil como fallback ou para acesso direto ao ranking sem o gráfico.
    """

    try:
        reference_date = ranking_repository.current_reference_date()
        result = ranking_repository.get(reference_date)
    except (RuntimeError, KeyError) as exc:
        raise HTTPException(
            status_code=404,
            detail=(
                "Nenhum ranking disponível. "
                "Execute o pipeline via /api/fr-price-series primeiro."
            ),
        ) from exc

    return result["ranking"]


# ===========================================================================
# /api/candlechart
# Gráfico 2 — Candlestick do ativo selecionado na tabela
# ===========================================================================


@router.get("/candlechart")
def get_candlechart(
    ticker: str = Query(..., description="Ticker do ativo selecionado na tabela"),
):
    """
    Gera o payload Plotly para o gráfico de candlestick de um ativo específico.

    Usa o histórico completo já cacheado no PriceRepository (inclui todos
    os indicadores técnicos calculados no passo 4 do init).

    Parâmetros
    ----------
    ticker : str
        Símbolo do ativo (ex.: PETR4). Case-insensitive.

    Retorno
    -------
    {
        "data"   : list[dict] — traces Plotly (candlestick, SMA, BBands, MACD, volume)
        "layout" : dict       — layout Plotly com subplots verticais
    }
    """

    # ------------------------------------------------------------------
    # 1. Recupera histórico de preços do cache
    # ------------------------------------------------------------------
    try:
        reference_date = price_repository.current_reference_date()
        prices = price_repository.get(reference_date)
    except (RuntimeError, KeyError) as exc:
        raise HTTPException(
            status_code=404,
            detail=(
                "Histórico de preços não encontrado. "
                "Execute o pipeline via /api/fr-price-series primeiro."
            ),
        ) from exc

    ticker = ticker.strip().upper()

    # ------------------------------------------------------------------
    # 2. Extrai slice do ativo selecionado
    # ------------------------------------------------------------------
    try:
        df_ticker = prices.xs(ticker, level="Ticker", axis=1).copy()
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"Ticker {ticker!r} não encontrado no histórico carregado.",
        )

    if df_ticker.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Ticker {ticker!r} não possui dados no período carregado.",
        )

    # Indicador de volume médio calculado aqui pois é específico da visualização
    df_ticker["volume_medio"] = df_ticker["Volume"].rolling(window=20).mean()

    # ------------------------------------------------------------------
    # 3. Delega montagem do payload ao chart builder
    # ------------------------------------------------------------------
    try:
        chart_payload = build_candle_chart_payload(df_ticker=df_ticker, ticker=ticker)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return chart_payload


# ===========================================================================
# /api/scatterchart
# Gráfico 3 — Dispersão Risco × Distância (todos os ativos ranqueados)
# ===========================================================================


@router.get("/scatterchart")
def get_scatterchart():
    """
    Retorna o payload Plotly para o gráfico de dispersão Risco × Distância,
    colorido por setor, com linhas de quadrante.

    Usa exclusivamente o ranking já cacheado no RankingRepository —
    nenhuma recomputação é realizada.

    O gráfico exibe todos os ativos ranqueados e é renderizado uma única vez,
    imediatamente após o pipeline ser concluído via /api/fr-price-series.

    Retorno
    -------
    {
        "data"   : list[dict] — traces Plotly (uma série por setor + linhas)
        "layout" : dict       — configuração do layout Plotly
    }
    """

    # ------------------------------------------------------------------
    # 1. Recupera o ranking cacheado
    # ------------------------------------------------------------------
    try:
        reference_date = ranking_repository.current_reference_date()
        result = ranking_repository.get(reference_date)
    except (RuntimeError, KeyError) as exc:
        raise HTTPException(
            status_code=404,
            detail=(
                "Nenhum ranking disponível. "
                "Execute o pipeline via /api/fr-price-series primeiro."
            ),
        ) from exc

    ranking = result.get("ranking", [])
    if not ranking:
        raise HTTPException(
            status_code=404,
            detail="Ranking vazio — nenhum ativo disponível para o gráfico de dispersão.",
        )

    # ------------------------------------------------------------------
    # 2. Delega montagem do payload ao chart builder
    # ------------------------------------------------------------------
    try:
        chart_payload = build_scatter_chart_payload(ranking=ranking)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return chart_payload
