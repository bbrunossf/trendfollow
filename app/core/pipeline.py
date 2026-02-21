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


def run_pipeline(reference_date: str | None = None) -> Dict[str, Any]:

    # ------------------------------------------------------------------
    # 1. Universo de ativos
    # ------------------------------------------------------------------
    tickers = list_b3_assets(
        min_price=config.MIN_PRICE,
        min_volume=config.MIN_VOLUME,
        excluded_suffixes=config.EXCLUDE_SUFFIXES
    )

    if not tickers:
        return {"summary": {"message": "Nenhum ativo encontrado"},
                "ranking": [], "charts": {}}

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
        return {"summary": {"message": "Histórico de preços vazio"},
                "ranking": [], "charts": {}}

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
    
    df_latest = extract_latest(prices, price_field="Adj Close", indicator_fields=None)
    df_latest['Ticker'] = df_latest['Ticker'].astype(str).str.strip().str.upper()

    # ------------------------------------------------------------------
    # 5. Resolução das datas válidas e snapshots
    # ------------------------------------------------------------------
    trading_dates = resolve_to_trading_dates(
        prices.index,
        theoretical_dates
    )
    
    #debug
    #print("datas válidas encontradas")
    #print(trading_dates) #names= Price, Ticker    
        
    print("preços:")    
    print(prices.head())    
    print("colunas do price")
    print(prices.columns)
    print("names")
    print(prices.columns.names)

    price_snapshots = extract_price_snapshots(
        prices,
        trading_dates,
        price_field="Adj Close"
    )
    #print("preços das datas selecionadas:")
    #print(price_snapshots)
    
    df = flatten_snapshot_for_scoring(price_snapshots)
    #aqui o df deixa de ser multiindex
    
    #########
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

    #########
    

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

    # Converte payload do ranking para DataFrame
    df_ranked = pd.DataFrame(ranking_result["payload"])
    df_ranked['ticker'] = df_ranked['ticker'].astype(str).str.strip().str.upper()
    
    
    #debug
    # print("df ranked:")
    # print(df_ranked.columns)
    # print(df_ranked.columns.names)
    
    # print("df_latest:")
    # print(df_latest.columns)
    # print(df_latest.columns.names)
    
    df_latest = df_latest.rename(columns={'Ticker': 'ticker'})

    # merge (left) para manter só os ativos do ranking, mas trazendo valores do df_latest
    df_ranked = df_ranked.merge(df_latest, on='ticker', how='left', validate='m:1')

    # ------------------------------------------------------------------
    # 8. Enriquecimento com metadados e high_52w (Etapa A)
    # ------------------------------------------------------------------
    df_enriched = enrich_with_metadata_and_52w_high(
        df=df_ranked,
        ticker_column="ticker"
    )

    # ------------------------------------------------------------------
    # 9. Indicadores customizados finais (risco e retorno)
    # ------------------------------------------------------------------
    df_final = calculate_risk_return_indicators(
        df=df_enriched,
        price_col="Adj Close",
        stop_col="STOP_ATR_14_1.5",
        high_52w_col="high_52w"
    )
    
    
    # ------------------------------------------------------------------
    # 10. Summary
    # ------------------------------------------------------------------
    summary = {
        "total_universe": len(tickers),
        "scored_assets": len(scored),
        "ranked_assets": len(ranking_result["payload"]),
        "reference_date": reference_date
    }

    #charts = {"candles": None, "scatter": None}
    charts = {
        "price_snapshots": price_snapshots,
    }
    
    # ------------------------------------------------------------------
    # Sanitize para JSON: substituir Inf/-Inf por NaN e NaN por None
    # ------------------------------------------------------------------    

    # substituir Inf/-Inf por NaN
    df_clean = df_final.replace([np.inf, -np.inf], np.nan)

    # opcional: log das colunas com valores não finitos antes da limpeza
    num = df_final.select_dtypes(include=[np.number])
    bad_mask = ~np.isfinite(num)
    if bad_mask.any().any():
        bad_cols = bad_mask.any()[bad_mask.any()].index.tolist()
        print("Colunas com valores não finitos:", bad_cols)

    # converter NaN para None para JSON compatível
    df_clean = df_clean.where(pd.notnull(df_clean), 0)

    # gerar records seguros para JSON
    ranking_records = df_clean.to_dict(orient="records")

    return {
        "summary": summary,
        "ranking": ranking_records,
        "charts": charts
    }


    # return {
        # "summary": summary,
        ##"ranking": ranking_result["payload"],
        # "ranking": df_final.to_dict(orient="records"),
        # "charts": charts
    # }
    
    
