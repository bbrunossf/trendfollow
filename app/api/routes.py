from fastapi import APIRouter, Query, HTTPException
from typing import Optional

import pandas as pd
from datetime import date

from app.core.pipeline import run_pipeline
from app.data.preprocessing import build_price_matrix_for_chart, build_plotly_payload
#from app.api.plotly_payload import build_plotly_payload  # ajuste se estiver em outro módulo

import app.config as config

router = APIRouter()


@router.get("/charts/fr-price-series")
def get_fr_price_series(
    reference_date: Optional[str] = Query(
        default=str(date.today()),
        description="Data de referência no formato YYYY-MM-DD"
    )
):
    """
    Endpoint para geração do gráfico de validação da Força Relativa (FR).

    Retorna um payload JSON pronto para consumo pelo Plotly JS.
    """

    # ------------------------------------------------------------------
    # 1. Executa pipeline
    # ------------------------------------------------------------------
    result = run_pipeline(reference_date=reference_date)

    if "charts" not in result or "price_snapshots" not in result["charts"]:
        raise HTTPException(
            status_code=500,
            detail="price_snapshots não disponível no pipeline"
        )

    price_snapshots = result["charts"]["price_snapshots"]

    ranking = result.get("ranking", [])
    if not ranking:
        raise HTTPException(
            status_code=404,
            detail="Nenhum ativo ranqueado"
        )

    # ------------------------------------------------------------------
    # 2. Extrai tickers selecionados
    # ------------------------------------------------------------------
    selected_tickers = [
        item["ticker"]
        for item in ranking
        if item.get("FR_rank", 0) >= config.MIN_FR
    ]

    if not selected_tickers:
        raise HTTPException(
            status_code=404,
            detail="Nenhum ativo atende ao critério mínimo de FR"
        )

    # ------------------------------------------------------------------
    # 3. Monta matriz de preços para o gráfico
    # ------------------------------------------------------------------
    df_chart = build_price_matrix_for_chart(
        price_snapshots=price_snapshots,
        selected_tickers=selected_tickers,
        price_field="Adj Close"
    )

    # ------------------------------------------------------------------
    # 4. Monta payload Plotly
    # ------------------------------------------------------------------
    plotly_data = build_plotly_payload(df_chart)

    layout = {
        "title": "Validação da Força Relativa (FR)",
        "xaxis": {
            "title": "Data",
            "type": "date"
        },
        "yaxis": {
            "title": "Preço Ajustado (Adj Close)",
            "tickformat": ".2f"
        },
        "hovermode": "closest",
        "legend": {
            "orientation": "h",
            "y": -0.3
        }
    }

    return {
        "data": plotly_data,
        "layout": layout
    }
    
@router.get("/ranking")
def api_ranking(reference_date: Optional[str] = Query(None)):
    """
    Retorna o ranking/resultados do pipeline como JSON (lista de objetos).
    O run_pipeline deve aceitar reference_date (ou adapte a chamada).
    """
    # chama o pipeline; ajuste assinatura se necessário
    result = run_pipeline(reference_date=reference_date)
    # result["ranking"] deve ser uma lista de dicts (orient='records')
    return result["ranking"]