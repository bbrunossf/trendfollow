from fastapi import APIRouter, Query, HTTPException
from typing import Optional

import pandas as pd
import numpy as np
from datetime import date

from app.core.pipeline import run_pipeline
from app.core.init import init
from app.core.price_repository import price_repository
from app.data.preprocessing import build_price_matrix_for_chart, build_plotly_payload

import app.config as config

router = APIRouter()


@router.get("/fr-price-series")
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
    # 1. Garante inicialização do histórico de preços (etapas 1–4)
    # ------------------------------------------------------------------
    # se ainda não existir histórico para a data, inicializa (etapas 1–4)
    if not price_repository.has(reference_date):
        prices = init(reference_date)
        price_repository.set(reference_date, prices)
    
    # recupera o histórico de preços já inicializado
    prices = price_repository.get(reference_date)

    # ------------------------------------------------------------------
    # 2. Executa pipeline de ranking / snapshots (etapas 5+)
    # ------------------------------------------------------------------
    
    # executa pipeline de ranking / snapshots (etapas 5+)
    result = run_pipeline(prices=prices, reference_date=reference_date)

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
def api_ranking():
    """
    Retorna o ranking/resultados do pipeline como JSON (lista de objetos).
    O run_pipeline deve aceitar reference_date (ou adapte a chamada).
    """
    # recupera a data de referência atualmente ativa
    reference_date = price_repository.current_reference_date()

    # garante que o histórico de preços exista
    if not price_repository.has(reference_date):
        prices = init(reference_date)
        price_repository.set(reference_date, prices)

    prices = price_repository.get(reference_date)

    result = run_pipeline(prices=prices, reference_date=reference_date)

    return result["ranking"]

@router.get("/candlechart")    
def get_candlechart(ticker: str = Query(..., description="Ticker do ativo selecionado")):
    """
    gera gráfico de candles a partir do ticker da linha selecionada na tabela.    
    usa o dataframe completo 'prices' com dados dos ativos selecionados.
    calcula os indicadores medias moveis, bandas de bollinger, STOP_ATR, risco e retorno_risco    
    Retorna um payload JSON pronto para consumo pelo Plotly JS.
    """        
    #pega o prices e extrai somente os ativos selecionados
    #faz um slice só do ativo selecionado
    #calcula os indicadores e adiciona no dataframe
    #monta o dataframe final (e salva em cache? poderia, porque o mesmo ticker pode ser selecionado de novo pelo usuário)
    #Monta payload Plotly
    
    reference_date = price_repository.current_reference_date()
    prices = price_repository.get(reference_date)
    ticker = ticker.strip().upper()    
    
    # slice do ativo selecionado preservando o eixo temporal
    df_ticker = prices.xs(ticker, level="Ticker", axis=1).copy()
    df_ticker["volume_medio"] = df_ticker['Volume'].rolling(window=20).mean()
    
    # print("estrutura final do df")
    # print(df_ticker.columns)
    
    if df_ticker.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Ticker {ticker} não encontrado no histórico carregado"
        )
    
    #falta selecionar as colunas e montar a estrutura esperada pelo plotly_data
    # ------------------------------------------------------------------
    # Seleção das colunas OHLC e preparação para Plotly
    # ------------------------------------------------------------------
    # garante ordenação temporal
    df_clean = df_ticker.sort_index()
    
    start_idx = 20
    # slice para ignorar período sem indicadores
    df_plot = df_clean.iloc[start_idx:]
        
    # Agora cada coluna pode ser convertida em lista sem erro ao gerar JSON
    datas = df_plot.index.to_pydatetime().tolist() # extrai eixo temporal
    open_prices = df_plot["Open"].astype(float).tolist()
    high_prices = df_plot["High"].astype(float).tolist()
    low_prices = df_plot["Low"].astype(float).tolist()
    close_prices = df_plot["Close"].astype(float).tolist()
    sma_20 = df_plot["SMA_20"].tolist() 
    bb_upper_20 = df_plot["BB_UPPER_20"].tolist()
    bb_lower_20 = df_plot["BB_LOWER_20"].tolist()
    macd = df_plot["MACD_12_26"].tolist()
    macd_signal = df_plot["MACD_SIGNAL_9"].tolist()
    macd_hist = df_plot["MACD_HIST_12_26_9"].tolist()
    stop_atr = df_plot["STOP_ATR_14_1.5"].tolist()
    volume = df_plot["Volume"].tolist()
    volume_medio = df_plot["volume_medio"].tolist()    
    
    
    
    plotly_data = []  # começa vazio e vai adicionando as traces

    # Candlestick no eixo principal (yaxis)
    print("adicionando candlestick")
    plotly_data.append({
        "type": "candlestick",
        "x": datas,
        "open": open_prices,
        "high": high_prices,
        "low": low_prices,
        "close": close_prices,
        "name": ticker,
        "yaxis": "y"
    })

    # SMA
    print("adicionando sma")
    plotly_data.append({
        "type": "scatter",
        "mode": "lines",
        "x": datas,
        "y": df_plot["SMA_20"].astype(float).tolist(),
        "name": "SMA",
        "line": {"color": "black"},
        "yaxis": "y"
    })

    # Upper Band
    print("adicionando bbands up")
    plotly_data.append({
        "type": "scatter",
        "mode": "lines",
        "x": datas,
        "y": df_plot["BB_UPPER_20"].astype(float).tolist(),
        "name": "Upper Band",
        "line": {"dash": "dash", "color": "gray"},
        "opacity": 0.5,
        "yaxis": "y"
    })

    # Lower Band com preenchimento
    print("adicionando bbands low")
    plotly_data.append({
        "type": "scatter",
        "mode": "lines",
        "x": datas,
        "y": df_plot["BB_LOWER_20"].astype(float).tolist(),
        "name": "Lower Band",
        "line": {"dash": "dash", "color": "gray"},
        "fill": "tonexty",
        "opacity": 0.5,
        "yaxis": "y"
    })

    # Volume no subplot (yaxis2)
    print("adicionando volume")
    plotly_data.append({
        "type": "bar",
        "x": datas,
        "y": df_plot["Volume"].tolist(),
        "marker": {
            "color": ["green" if c > o else "red" for o, c in zip(open_prices, close_prices)]
        },
        "name": "Volume",
        "yaxis": "y2",
        "showlegend": False
    })
    
    # Volume Médio
    plotly_data.append({
        "type": "scatter",
        "mode": "lines",
        "x": datas,
        "y": volume_medio,
        "name": "Volume Médio",
        "line": {"color": "blue"},
        "yaxis": "y2"
    })

    # STOP ATR
    plotly_data.append({
        "type": "scatter",
        "mode": "lines",
        "x": datas,
        "y": df_plot["STOP_ATR_14_1.5"].tolist(),
        "name": "STOP ATR",
        "line": {"shape": "hv", "color": "red"},
        "yaxis": "y"
    })
    
    # MACD
    print("adicionando MACD")
    plotly_data.append({
        "type": "scatter",
        "mode": "lines",
        "x": datas,
        "y": df_plot["MACD_12_26"].tolist(),
        "name": "MACD",
        "line": {"color": "black"},
        "yaxis": "y3"
    })

    plotly_data.append({
        "type": "scatter",
        "mode": "lines",
        "x": datas,
        "y": df_plot["MACD_SIGNAL_9"].tolist(),
        "name": "MACD Signal",
        "line": {"dash": "dash", "color": "gray"},
        "opacity": 0.5,
        "yaxis": "y3"
    })

    plotly_data.append({
        "type": "bar",
        "x": datas,
        "y": df_plot["MACD_HIST_12_26_9"].tolist(),
        "name": "MACD Hist",
        "marker": {"color": "gray"},
        "yaxis": "y3"
    })


    # Layout com domínio vertical separado
    layout = {
        "height": 650,
        "title": f"Candlestick – {ticker}",
        "xaxis": {
            "title": "Data",
            "type": "date",
            "rangeslider": {"visible": False},
            "rangebreaks": [{"bounds": ["sat", "mon"]}]
        },
        "yaxis": {  # Candlestick + indicadores principais
            "title": "Preço",
            "domain": [0.3, 1],  # ocupa 70% da altura,
            "autorange": True,
            "rangemode": "normal"
        },
        "yaxis2": {  # Volume
            "title": "Volume",
            "domain": [0.15, 0.3],  # ocupa 30% inferior
            "showgrid": False
        },
        "yaxis3": {  # MACD
            "title": "MACD",
            "domain": [0, 0.15],  # ocupa 30% inferior
            "showgrid": False
        },
        "hovermode": "x unified"
    }

    return {
        "data": plotly_data,
        "layout": layout
    }
    
        
    
    
        
     