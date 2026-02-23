# """
# Pipeline central da aplicação.

# Responsável por orquestrar:
# - download de dados
# - cálculo de indicadores
# - preparação o dataframe completo que será usado posteriormente
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


def init(reference_date: str | None = None) -> pd.DataFrame:
    """
    Pipeline base (etapas 1–4).

    Responsável por:
    - definir universo de ativos
    - baixar histórico de preços
    - normalizar dados
    - calcular indicadores técnicos
    """
    print("iniciando função")

    # ------------------------------------------------------------------
    # 1. Universo de ativos
    # ------------------------------------------------------------------
    tickers = list_b3_assets(
        min_price=config.MIN_PRICE,
        min_volume=config.MIN_VOLUME,
        excluded_suffixes=config.EXCLUDE_SUFFIXES
    )
    #print(tickers)

    if not tickers:
        raise RuntimeError("Nenhum ativo encontrado para os filtros definidos")
    # else:
        # print("tickers obtidos")

    # ------------------------------------------------------------------
    # 2. Datas teóricas e janela mínima
    # ------------------------------------------------------------------
    theoretical_dates = generate_theoretical_dates(
        reference_date or pd.Timestamp.today(),
        periods=config.ANALYSIS_MONTHS + 1
    )

    start_date, end_date = get_download_window(theoretical_dates)

    # ------------------------------------------------------------------
    # 3. Download único do histórico
    # ------------------------------------------------------------------
    prices = download_price_history(
        tickers=tickers,
        start=start_date,
        end=end_date,
        progress=True
    )

    if prices.empty:
        raise RuntimeError("Histórico de preços vazio")

    prices = normalize_price_columns(prices) #normalizar é tratar o multiindex

    # ------------------------------------------------------------------
    # 4. Indicadores técnicos (histórico completo)
    # ------------------------------------------------------------------
    prices = simple_moving_average(
        prices,
        price_field="Adj Close",
        window=config.MA_WINDOW
    )

    prices = calculate_bollinger_bands(
        prices,
        window=config.BOLLINGER_WINDOW,
        num_std=config.BOLLINGER_STD
    )

    prices = calculate_macd(
        prices,
        fast_window=config.MACD_FAST,
        slow_window=config.MACD_SLOW,
        signal_window=config.MACD_SIGNAL
    )

    prices = calculate_atr_and_stop(
        prices,
        window=config.ATR_WINDOW,
        multiplier=config.ATR_MULTIPLIER
    )    
    #debug
    prices.to_clipboard()
    
    # ------------------------------------------------------------------
    # 10. Sanitização para JSON e montagem do payload
    # ------------------------------------------------------------------
    df_clean = prices.copy()
    df_clean.replace([np.nan, np.inf, -np.inf], 0, inplace=True) #aqui está substituindo por zero
    #df_clean = df_clean.fillna(np.nan).replace([np.nan, np.inf, -np.inf], [None, None, None]) #aqui substitui por None, mas dá errado ainda

                    
    return df_clean