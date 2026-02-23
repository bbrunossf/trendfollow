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
from typing import Iterable, List, Optional, Literal

from datetime import datetime
from dateutil.relativedelta import relativedelta
from brapi import Brapi



BRAPI_BASE_URL = "https://brapi.dev/api"
BRAPI_STOCK_LIST_ENDPOINT = "/quote/list"
BRAPI_TOKEN = "ikKPyJs6dZwA3GUp2SX46z"


def list_b3_assets(min_price: float = 4.0,
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
    client = Brapi(
        api_key=BRAPI_TOKEN, 
        environment="production",
    )
    stocks = client.quote.list()
    #change, stock, sector, name, close, logo, type, market_cap, volume
    data=[]
    for stock in stocks.stocks: #para cada ativo, retornar nome/ticket, close, volume
        data.append({
            "ticket": stock.stock,
            "name": stock.name,
            "close": stock.close,
            "sector": stock.sector,
            "volume": stock.volume
        })

    df = pd.DataFrame.from_dict(data) #cria dataframe a partir do dict data
    print(df.head())
    dff = df[ (df['volume'] > min_volume) &  (df['close'] > min_price) ]
    dff = dff[['ticket', 'name', 'close', 'sector', 'volume']].sort_values(by='ticket')
    substring = ['11', '32']
    dff_negative = dff['ticket'].str.contains('|'.join(substring))
    dff = dff[~dff_negative]
    
    sfx = '.SA' #incluir o sufixo .SA
    acoess = dff['ticket'].apply(lambda x: f"{x}{sfx}").values.tolist()         
    #print(acoess[0:10])
    return sorted(acoess) #só preciso dos nomes das ações filtradas pelo preço e volume



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
                     group_by="column",
                     multi_level_index=False, #mantem df simples, sem multinivel
                     progress=progress)

    if df.empty:
        raise RuntimeError("Nenhum dado retornado pelo yfinance.")

    #debug
    #print("====DEBUG====")
    #print(df.columns)
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




def get_price_history(
    tickers: Iterable[str],
    period_months: int,
    reference_date: str | None = None,
    group_by_ticker: bool = False,
    auto_adjust: bool = False
) -> pd.DataFrame:
    """
    Função de alto nível para obter histórico de preços a partir de um período em meses.

    Esta função é um adaptador entre o pipeline e o yfinance.
    """

    if reference_date:
        end_date = datetime.strptime(reference_date, "%Y-%m-%d")
    else:
        end_date = datetime.today()

    start_date = end_date - relativedelta(months=period_months)

    return download_price_history(
        tickers=tickers,
        start=start_date.strftime("%Y-%m-%d"),
        end=end_date.strftime("%Y-%m-%d"),
        group_by_ticker=group_by_ticker,
        auto_adjust=auto_adjust,
        progress=True
    )

def normalize_price_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Garante que o DataFrame de preços tenha colunas MultiIndex nomeadas
    como ('Field', 'Ticker').
    """
    if not isinstance(df.columns, pd.MultiIndex):
        raise ValueError("Esperado DataFrame com colunas MultiIndex.")

    if df.columns.names != ["Field", "Ticker"]:
        df.columns = df.columns.set_names(["Field", "Ticker"])

    return df


def generate_theoretical_dates(
    reference_date: str | pd.Timestamp,
    periods: int = 6,
    spacing_days: int = 30
) -> list[pd.Timestamp]:
    """
    Gera datas teóricas espaçadas aproximadamente em meses,
    incluindo a data de referência.
    """
    if isinstance(reference_date, str):
        reference_date = pd.Timestamp(reference_date)

    return [
        reference_date - pd.Timedelta(days=i * spacing_days)
        for i in range(periods)
    ]

def get_download_window(
    theoretical_dates: list[pd.Timestamp]
) -> tuple[pd.Timestamp, pd.Timestamp]:
    """
    Retorna o intervalo mínimo necessário para download.
    """
    return min(theoretical_dates), max(theoretical_dates)




def enrich_with_metadata_and_52w_high(
    df: pd.DataFrame,
    ticker_column: str = "ticker",
    history_period: Literal["1y"] = "1y",
    high_col_name: str = "high_52w",
) -> pd.DataFrame:
    """
    Adiciona metadados e o preço máximo das últimas 52 semanas a um DataFrame.

    Parâmetros
    ----------
    df
        DataFrame que contém a coluna de tickers e já possui indicadores calculados.
    ticker_column
        Nome da coluna do DataFrame que contém os tickers.
    history_period
        Período usado para baixar o histórico de preço (deve cobrir as últimas 52 semanas).
        '1y' é suportado pela yfinance 1.2.0.
    high_col_name
        Nome da coluna que conterá o máximo das últimas 52 semanas.

    Retorna
    -------
    pd.DataFrame
        Uma cópia do DataFrame original, com colunas extras:
        - industry
        - sector
        - symbol
        - shortName
        - high_52w
    """
    enriched_rows = []

    for ticker in df[ticker_column].unique():
        # cria objeto yfinance
        yf_ticker = yf.Ticker(ticker)

        # metadados
        info = yf_ticker.info

        industry = info.get("industry")
        sector = info.get("sector")
        symbol = info.get("symbol")
        short_name = info.get("shortName")

        # histórico 1 ano para extrair high de 52 semanas
        hist = yf_ticker.history(period=history_period, auto_adjust=True)

        # extrai máximo; se não houver dados, deixa como NaN
        high_52w = (
            hist["High"].max() if "High" in hist.columns and not hist.empty else None
        )

        enriched_rows.append(
            {
                "ticker": ticker,
                "industry": industry,
                "sector": sector,
                "symbol": symbol,
                "shortName": short_name,
                high_col_name: high_52w,
            }
        )

    # transforma em DataFrame de metadados
    metadata_df = pd.DataFrame(enriched_rows)
    
    

    # faz join com df original
    df_enriched = df.merge(metadata_df, how="left", on="ticker") #não junta porque em um df está 'ticker' e no outro está 'Ticker'
    
    #debug
    #print("dataframe enriquecido:")
    #print(df_enriched)
    #print(df_enriched.columns)
    

    return df_enriched
