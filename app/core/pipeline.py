"""
Pipeline central da aplicação.

Responsável por orquestrar:
- download de dados
- cálculo de indicadores
- scoring
- ranking
- preparação de payload para API / frontend
"""

from typing import Dict, Any
import pandas as pd

from app.data.market_data import (get_all_tickers, get_price_history,
                                  get_stock_metadata)

from app.services.scoring import calculate_relative_strength
from app.services.ranking import build_ranking

from app.finance.moving_averages import add_moving_average
from app.finance.bollinger import calculate_bollinger_bands
from app.finance.macd import calculate_macd
from app.finance.volatility import calculate_atr_and_stop

import app.config as config


def run_pipeline(reference_date: str | None = None) -> Dict[str, Any]:
    """
    Executa o pipeline completo do sistema.

    Parâmetros
    ----------
    reference_date : str | None
        Data de referência para o cálculo (YYYY-MM-DD).
        Se None, usa a data atual.

    Retorno
    -------
    dict
        Estrutura completa pronta para API:
        {
            "summary": dict,
            "ranking": list[dict],
            "charts": dict
        }
    """

    # ------------------------------------------------------------------
    # 1. Universo de ativos
    # ------------------------------------------------------------------
    tickers = get_all_tickers(min_price=config.MIN_PRICE,
                              min_volume=config.MIN_VOLUME,
                              exclude_suffixes=config.EXCLUDE_SUFFIXES)

    if not tickers:
        return {
            "summary": {
                "message": "Nenhum ativo encontrado"
            },
            "ranking": [],
            "charts": {}
        }

    # ------------------------------------------------------------------
    # 2. Histórico de preços
    # ------------------------------------------------------------------
    prices = get_price_history(tickers=tickers,
                               period_months=config.LOOKBACK_MONTHS,
                               reference_date=reference_date)

    if prices.empty:
        return {
            "summary": {
                "message": "Histórico de preços vazio"
            },
            "ranking": [],
            "charts": {}
        }

    # ------------------------------------------------------------------
    # 3. Cálculo de indicadores básicos
    # ------------------------------------------------------------------
    prices = add_moving_average(prices, window=config.MA_WINDOW)

    prices = calculate_bollinger_bands(prices,
                                       window=config.BB_WINDOW,
                                       num_std=config.BB_STD)

    prices = calculate_macd(prices,
                            fast=config.MACD_FAST,
                            slow=config.MACD_SLOW,
                            signal=config.MACD_SIGNAL)

    prices = calculate_atr_and_stop(prices,
                                    window=config.ATR_WINDOW,
                                    multiplier=config.ATR_MULTIPLIER)

    # ------------------------------------------------------------------
    # 4. Scoring (Força Relativa)
    # ------------------------------------------------------------------
    scored = calculate_relative_strength(
        prices, lookback_months=config.LOOKBACK_MONTHS)

    if scored.empty:
        return {
            "summary": {
                "message": "Nenhum ativo pontuado"
            },
            "ranking": [],
            "charts": {}
        }

    # ------------------------------------------------------------------
    # 5. Ranking
    # ------------------------------------------------------------------
    ranking_result = build_ranking(
        df=scored,
        score_column="FR",
        min_score=config.MIN_FR,
        top_n=config.TOP_N,
        payload_fields=["ticker", "FR", "close", "sector", "atr", "stop_atr"])

    # ------------------------------------------------------------------
    # 6. Metadados (opcional, enriquecimento)
    # ------------------------------------------------------------------
    metadata = get_stock_metadata(
        [item["ticker"] for item in ranking_result["payload"]])

    # ------------------------------------------------------------------
    # 7. Summary
    # ------------------------------------------------------------------
    summary = {
        "total_universe": len(tickers),
        "scored_assets": len(scored),
        "ranked_assets": len(ranking_result["payload"]),
        "reference_date": reference_date
    }

    # ------------------------------------------------------------------
    # 8. Charts (placeholder)
    # ------------------------------------------------------------------
    charts = {"candles": None, "scatter": None}

    return {
        "summary": summary,
        "ranking": ranking_result["payload"],
        "charts": charts,
        "metadata": metadata
    }
