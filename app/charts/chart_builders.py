"""
chart_builders.py

Responsável pela montagem de payloads Plotly prontos para consumo pelo frontend.

Responsabilidades:
- receber DataFrames já calculados (preços, indicadores, ranking)
- estruturar traces e layouts no formato esperado pelo Plotly JS
- retornar dicts serializáveis (JSON-safe)

Este módulo NÃO:
- baixa dados de mercado
- calcula indicadores técnicos
- executa scoring ou ranking
- conhece endpoints ou detalhes de HTTP
"""

from typing import Any, Dict, List

import numpy as np
import pandas as pd

import app.config as config
from app.data.preprocessing import build_plotly_payload, build_price_matrix_for_chart

# ===========================================================================
# Gráfico 1 — Força Relativa (linha por ativo ranqueado)
# ===========================================================================


def build_fr_chart_payload(
    price_snapshots: pd.DataFrame,
    ranking: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Monta o payload Plotly para o gráfico de validação da Força Relativa.

    Parâmetros
    ----------
    price_snapshots : pd.DataFrame
        DataFrame MultiIndex (Field, Ticker) com snapshots de preço
        nas datas resolvidas, produzido por build_ranking_result.
    ranking : list[dict]
        Lista de ativos ranqueados retornada por build_ranking_result,
        cada item contendo ao menos as chaves "ticker" e "FR_rank".

    Retorno
    -------
    dict com as chaves:
    - "data"   : list[dict] — traces Plotly
    - "layout" : dict       — configuração do layout Plotly
    """

    if price_snapshots is None or (
        hasattr(price_snapshots, "empty") and price_snapshots.empty
    ):
        raise ValueError("price_snapshots está vazio ou None")

    if not ranking:
        raise ValueError("ranking está vazio")

    # ------------------------------------------------------------------
    # Filtra tickers que atendem ao critério mínimo de FR_rank
    # ------------------------------------------------------------------
    selected_tickers = [
        item["ticker"] for item in ranking if item.get("FR_rank", 0) >= config.MIN_FR
    ]

    if not selected_tickers:
        raise ValueError(
            f"Nenhum ativo atende ao critério mínimo de FR_rank >= {config.MIN_FR}"
        )

    # ------------------------------------------------------------------
    # Monta matriz de preços (ticker × datas) para o gráfico
    # ------------------------------------------------------------------
    df_chart = build_price_matrix_for_chart(
        price_snapshots=price_snapshots,
        selected_tickers=selected_tickers,
        price_field="Adj Close",
    )

    # ------------------------------------------------------------------
    # Converte para traces Plotly
    # ------------------------------------------------------------------
    plotly_data = build_plotly_payload(df_chart)

    layout = {
        "title": "Validação da Força Relativa (FR)",
        "xaxis": {
            "title": "Data",
            "type": "date",
        },
        "yaxis": {
            "title": "Preço Ajustado (Adj Close)",
            "tickformat": ".2f",
        },
        "hovermode": "closest",
        "legend": {
            "orientation": "h",
            "y": -0.3,
        },
    }

    return {
        "data": plotly_data,
        "layout": layout,
    }


# ===========================================================================
# Gráfico 2 — Candlestick (ativo selecionado na tabela)
# ===========================================================================


def build_candle_chart_payload(
    df_ticker: pd.DataFrame,
    ticker: str,
    start_idx: int = 20,
) -> Dict[str, Any]:
    """
    Monta o payload Plotly para o gráfico de candlestick de um ativo específico.

    Parâmetros
    ----------
    df_ticker : pd.DataFrame
        Slice do histórico referente ao ativo, com índice DatetimeIndex e colunas:
        Open, High, Low, Close, Volume, Adj Close, SMA_20, BB_UPPER_20,
        BB_LOWER_20, MACD_12_26, MACD_SIGNAL_9, MACD_HIST_12_26_9,
        STOP_ATR_14_1.5.
        Deve já conter a coluna "volume_medio" calculada externamente.
    ticker : str
        Símbolo do ativo (ex.: "PETR4").
    start_idx : int
        Quantidade de linhas iniciais a descartar para eliminar o período
        sem indicadores calculados. Default: 20.

    Retorno
    -------
    dict com as chaves:
    - "data"   : list[dict] — traces Plotly
    - "layout" : dict       — configuração do layout Plotly
    """

    if df_ticker is None or df_ticker.empty:
        raise ValueError(f"DataFrame vazio recebido para o ticker {ticker!r}")

    # ------------------------------------------------------------------
    # Prepara o slice final (ordenado, sem período sem indicadores)
    # ------------------------------------------------------------------
    df_plot = df_ticker.sort_index().iloc[start_idx:]

    # Eixo temporal e séries numéricas
    datas = df_plot.index.to_pydatetime().tolist()
    open_prices = df_plot["Open"].astype(float).tolist()
    high_prices = df_plot["High"].astype(float).tolist()
    low_prices = df_plot["Low"].astype(float).tolist()
    close_prices = df_plot["Close"].astype(float).tolist()
    volume = df_plot["Volume"].tolist()
    volume_medio = df_plot["volume_medio"].tolist()

    # Cores de volume: verde se fechamento > abertura, vermelho caso contrário
    volume_colors = [
        "green" if c > o else "red" for o, c in zip(open_prices, close_prices)
    ]

    # ------------------------------------------------------------------
    # Montagem das traces
    # ------------------------------------------------------------------
    plotly_data = []

    # Candlestick principal
    plotly_data.append(
        {
            "type": "candlestick",
            "x": datas,
            "open": open_prices,
            "high": high_prices,
            "low": low_prices,
            "close": close_prices,
            "name": ticker,
            "yaxis": "y",
        }
    )

    # Média Móvel Simples
    plotly_data.append(
        {
            "type": "scatter",
            "mode": "lines",
            "x": datas,
            "y": df_plot["SMA_20"].astype(float).tolist(),
            "name": "SMA 20",
            "line": {"color": "black"},
            "yaxis": "y",
        }
    )

    # Banda Superior de Bollinger
    plotly_data.append(
        {
            "type": "scatter",
            "mode": "lines",
            "x": datas,
            "y": df_plot["BB_UPPER_20"].astype(float).tolist(),
            "name": "Upper Band",
            "line": {"dash": "dash", "color": "gray"},
            "opacity": 0.5,
            "yaxis": "y",
        }
    )

    # Banda Inferior de Bollinger (com preenchimento até a banda superior)
    plotly_data.append(
        {
            "type": "scatter",
            "mode": "lines",
            "x": datas,
            "y": df_plot["BB_LOWER_20"].astype(float).tolist(),
            "name": "Lower Band",
            "line": {"dash": "dash", "color": "gray"},
            "fill": "tonexty",
            "opacity": 0.5,
            "yaxis": "y",
        }
    )

    # STOP ATR
    plotly_data.append(
        {
            "type": "scatter",
            "mode": "lines",
            "x": datas,
            "y": df_plot["STOP_ATR_14_1.5"].tolist(),
            "name": "STOP ATR",
            "line": {"shape": "hv", "color": "red"},
            "yaxis": "y",
        }
    )

    # Volume (barras)
    plotly_data.append(
        {
            "type": "bar",
            "x": datas,
            "y": volume,
            "marker": {"color": volume_colors},
            "name": "Volume",
            "yaxis": "y2",
            "showlegend": False,
        }
    )

    # Volume Médio (linha)
    plotly_data.append(
        {
            "type": "scatter",
            "mode": "lines",
            "x": datas,
            "y": volume_medio,
            "name": "Volume Médio",
            "line": {"color": "blue"},
            "yaxis": "y2",
        }
    )

    # MACD — linha principal
    plotly_data.append(
        {
            "type": "scatter",
            "mode": "lines",
            "x": datas,
            "y": df_plot["MACD_12_26"].tolist(),
            "name": "MACD",
            "line": {"color": "black"},
            "yaxis": "y3",
        }
    )

    # MACD — linha de sinal
    plotly_data.append(
        {
            "type": "scatter",
            "mode": "lines",
            "x": datas,
            "y": df_plot["MACD_SIGNAL_9"].tolist(),
            "name": "MACD Signal",
            "line": {"dash": "dash", "color": "gray"},
            "opacity": 0.5,
            "yaxis": "y3",
        }
    )

    # MACD — histograma
    plotly_data.append(
        {
            "type": "bar",
            "x": datas,
            "y": df_plot["MACD_HIST_12_26_9"].tolist(),
            "name": "MACD Hist",
            "marker": {"color": "gray"},
            "yaxis": "y3",
        }
    )

    # ------------------------------------------------------------------
    # Layout com subplots verticais
    # ------------------------------------------------------------------
    layout = {
        "height": 650,
        "title": f"Candlestick — {ticker}",
        "xaxis": {
            "title": "Data",
            "type": "date",
            "rangeslider": {"visible": False},
            "rangebreaks": [{"bounds": ["sat", "mon"]}],
        },
        "yaxis": {  # Candlestick + indicadores de preço
            "title": "Preço",
            "domain": [0.3, 1],
            "autorange": True,
            "rangemode": "normal",
        },
        "yaxis2": {  # Volume
            "title": "Volume",
            "domain": [0.15, 0.3],
            "showgrid": False,
        },
        "yaxis3": {  # MACD
            "title": "MACD",
            "domain": [0, 0.15],
            "showgrid": False,
        },
        "hovermode": "x unified",
    }

    return {
        "data": plotly_data,
        "layout": layout,
    }


# ===========================================================================
# Gráfico 3 — Dispersão Risco × Distância (todos os ativos ranqueados)
# ===========================================================================


def build_scatter_chart_payload(
    ranking: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Monta o payload Plotly para o gráfico de dispersão Risco × Distância,
    colorido por setor, com linhas de quadrante.

    Fonte de dados: list[dict] retornada por build_ranking_result,
    que já contém os campos calculados por calculate_risk_return_indicators
    e enrich_with_metadata_and_52w_high.

    Campos consumidos por ativo
    ---------------------------
    - distancia    : distância percentual até o topo de 52 semanas (eixo X)
    - Risco_%      : risco percentual até o STOP ATR              (eixo Y)
    - sector       : setor de atuação (cor da série)
    - ticker       : rótulo de texto sobre o ponto
    - Retorno_Risco: relação retorno/risco (hover)

    Parâmetros
    ----------
    ranking : list[dict]
        Lista de ativos ranqueados, com os campos acima.

    Retorno
    -------
    dict com as chaves:
    - "data"   : list[dict] — traces Plotly (uma série por setor + linhas)
    - "layout" : dict       — configuração do layout Plotly
    """

    if not ranking:
        raise ValueError("ranking está vazio")

    df = pd.DataFrame(ranking)

    required_cols = ["distancia", "Risco_%", "ticker"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(
            f"Colunas obrigatórias ausentes no ranking: {missing}. "
            "Verifique se calculate_risk_return_indicators foi executado."
        )

    # Remove ativos sem os campos numéricos essenciais
    df = df.dropna(subset=["distancia", "Risco_%"])

    if df.empty:
        raise ValueError(
            "Nenhum ativo possui 'distancia' e 'Risco_%' válidos para o gráfico."
        )

    # Garante coluna de setor preenchida
    if "sector" not in df.columns:
        df["sector"] = "N/D"
    df["sector"] = df["sector"].fillna("N/D").astype(str)

    # Garante coluna de Retorno_Risco preenchida
    if "Retorno_Risco" not in df.columns:
        df["Retorno_Risco"] = np.nan
    df["Retorno_Risco"] = df["Retorno_Risco"].fillna(float("nan"))

    # ------------------------------------------------------------------
    # Pontos de corte dos quadrantes
    # ------------------------------------------------------------------
    x_min = float(df["distancia"].to_numpy(dtype=float).min())
    x_max = float(df["distancia"].to_numpy(dtype=float).max())
    y_min = float(df["Risco_%"].to_numpy(dtype=float).min())
    y_max = float(df["Risco_%"].to_numpy(dtype=float).max())

    mid_x = x_max / 2
    mid_y = y_max / 2

    # ------------------------------------------------------------------
    # Traces: uma série por setor (permite legenda interativa por cor)
    # ------------------------------------------------------------------
    plotly_data = []

    for sector in sorted(df["sector"].unique()):
        df_sector = df[df["sector"] == sector].copy()

        retorno_risco_values = [
            round(v, 2) if isinstance(v, float) and np.isfinite(v) else None
            for v in df_sector["Retorno_Risco"].tolist()
        ]

        plotly_data.append(
            {
                "type": "scatter",
                "mode": "markers+text",
                "name": sector,
                "x": df_sector["distancia"].tolist(),
                "y": df_sector["Risco_%"].tolist(),
                "text": df_sector["ticker"].tolist(),
                "textposition": "bottom right",
                "customdata": retorno_risco_values,
                "marker": {"size": 10},
                "hovertemplate": (
                    "<b>%{text}</b><br>"
                    "Distância: %{x:.2f}%<br>"
                    "Risco: %{y:.2f}%<br>"
                    "Retorno/Risco: %{customdata:.2f}"
                    "<extra>%{fullData.name}</extra>"
                ),
            }
        )

    # ------------------------------------------------------------------
    # Linha vertical — divide o eixo X no ponto médio
    # ------------------------------------------------------------------
    plotly_data.append(
        {
            "type": "scatter",
            "mode": "lines",
            "x": [mid_x, mid_x],
            "y": [y_min - 1, y_max + 1],
            "line": {"color": "red", "dash": "dash"},
            "showlegend": False,
            "hoverinfo": "skip",
        }
    )

    # ------------------------------------------------------------------
    # Linha horizontal — divide o eixo Y no ponto médio
    # ------------------------------------------------------------------
    plotly_data.append(
        {
            "type": "scatter",
            "mode": "lines",
            "x": [x_min - 1, x_max + 1],
            "y": [mid_y, mid_y],
            "line": {"color": "red", "dash": "dash"},
            "showlegend": False,
            "hoverinfo": "skip",
        }
    )

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    layout = {
        "title": "Dispersão por Setor — Risco × Distância do Topo (52 semanas)",
        "height": 500,
        "xaxis": {
            "title": "Distância até o Topo de 52 semanas (%)",
            "zeroline": False,
        },
        "yaxis": {
            "title": "Risco até o STOP ATR (%)",
            "zeroline": False,
        },
        "hovermode": "closest",
        "legend": {
            "title": {"text": "Setor"},
            "orientation": "v",
        },
    }

    return {
        "data": plotly_data,
        "layout": layout,
    }
