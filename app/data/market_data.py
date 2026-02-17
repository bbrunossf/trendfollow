"""
market_data.py

Camada responsável exclusivamente pela obtenção e padronização
de dados de mercado.

Fontes:
- BRAPI: listagem completa de ativos da B3
- yfinance: preços históricos e metadados dos ativos

Este módulo NÃO aplica indicadores técnicos, filtros de estratégia
ou regras de decisão.
"""

from __future__ import annotations

import requests
import pandas as pd
import yfinance as yf
from typing import Iterable, List, Optional

BRAPI_BASE_URL = "https://brapi.dev/api"
BRAPI_STOCK_LIST_ENDPOINT = "/quote/list"


def list_b3_assets(min_price: float = 5.0,
                   min_volume: float = 1_000_000,
                   excluded_suffixes: Iterable[str] = ("11", "32"),
                   add_yfinance_suffix: bool = True,
                   timeout: int = 30) -> List[str]:
    """
    Obtém a lista completa de ativos da B3 via BRAPI e aplica filtros básicos.

    Parâmetros
    ----------
    min_price : float, default=5.0
        Preço mínimo do ativo.

    min_volume : float, default=1_000_000
        Volume financeiro mínimo.

    excluded_suffixes : Iterable[str], default=("11", "32")
        Sufixos de tickers a serem excluídos.

    add_yfinance_suffix : bool, default=True
        Adiciona o sufixo '.SA' aos tickers para compatibilidade com yfinance.

    timeout : int, default=30
        Timeout da requisição HTTP.

    Retorno
    -------
    list[str]
        Lista de tickers filtrados e padronizados.
    """
    url = f"{BRAPI_BASE_URL}{BRAPI_STOCK_LIST_ENDPOINT}"

    response = requests.get(url, timeout=timeout)
    response.raise_for_status()

    data = response.json()

    stocks = data.get("stocks", [])

    filtered = []

    for stock in stocks:
        symbol = stock.get("stock")
        price = stock.get("close")
        volume = stock.get("volume")

        if not symbol or price is None or volume is None:
            continue

        if price < min_price or volume < min_volume:
            continue

        if any(symbol.endswith(suffix) for suffix in excluded_suffixes):
            continue

        ticker = f"{symbol}.SA" if add_yfinance_suffix else symbol
        filtered.append(ticker)

    return sorted(filtered)


def download_price_history(tickers: Iterable[str],
                           start: str,
                           end: str,
                           group_by_ticker: bool = False,
                           auto_adjust: bool = False,
                           progress: bool = False) -> pd.DataFrame:
    """
    Baixa o histórico de preços dos ativos via yfinance.

    Parâmetros
    ----------
    tickers : Iterable[str]
        Lista de tickers no padrão yfinance (ex.: PETR4.SA).

    start : str
        Data inicial (YYYY-MM-DD).

    end : str
        Data final (YYYY-MM-DD).

    group_by_ticker : bool, default=False
        Se True, retorna colunas agrupadas por ticker.

    auto_adjust : bool, default=False
        Se True, ajusta preços automaticamente (dividendos/splits).

    progress : bool, default=False
        Exibe barra de progresso do yfinance.

    Retorno
    -------
    pandas.DataFrame
        DataFrame com dados OHLCV.
        Pode ser multi-indexado, dependendo do parâmetro group_by_ticker.
    """
    if not tickers:
        raise ValueError("A lista de tickers está vazia.")

    df = yf.download(tickers=list(tickers),
                     start=start,
                     end=end,
                     auto_adjust=auto_adjust,
                     group_by="ticker" if group_by_ticker else "column",
                     progress=progress)

    if df.empty:
        raise RuntimeError("Nenhum dado retornado pelo yfinance.")

    return df


def get_asset_metadata(tickers: Iterable[str],
                       fields: Optional[Iterable[str]] = None) -> pd.DataFrame:
    """
    Obtém metadados dos ativos via yfinance.

    Parâmetros
    ----------
    tickers : Iterable[str]
        Lista de tickers.

    fields : Iterable[str], optional
        Campos desejados. Se None, usa um conjunto padrão.

    Retorno
    -------
    pandas.DataFrame
        DataFrame tabular com metadados dos ativos.
    """
    default_fields = ("longName", "sector", "industry", "marketCap",
                      "fiftyTwoWeekHigh", "fiftyTwoWeekLow", "currency",
                      "exchange")

    fields = fields or default_fields

    records = []

    for ticker in tickers:
        try:
            info = yf.Ticker(ticker).info
        except Exception:
            continue

        record = {"ticker": ticker}

        for field in fields:
            record[field] = info.get(field)

        records.append(record)

    if not records:
        raise RuntimeError("Nenhum metadado foi obtido.")

    return pd.DataFrame.from_records(records)
