"""
macd.py

Cálculo do indicador MACD (Moving Average Convergence Divergence)
utilizando apenas pandas, sem dependências externas.

O módulo é intencionalmente desacoplado de qualquer lógica de visualização.
"""

from typing import Union
import pandas as pd


def calculate_macd(
    df: pd.DataFrame,
    price_field: str = "Adj Close",
    fast_window: int = 12,
    slow_window: int = 26,
    signal_window: int = 9
) -> pd.DataFrame:
    """
    Calcula o indicador MACD para múltiplos ativos a partir de um DataFrame
    com colunas MultiIndex (Field, Ticker).

    Colunas adicionadas:
    - MACD_<fast>_<slow>
    - MACD_SIGNAL_<signal>
    - MACD_HIST_<fast>_<slow>_<signal>

    Parâmetros
    ----------
    df : pandas.DataFrame
        DataFrame com dados de mercado no padrão MultiIndex.

    price_field : str, default="Close"
        Campo de preço utilizado no cálculo.

    fast_window : int, default=12
        Janela da média móvel exponencial rápida.

    slow_window : int, default=26
        Janela da média móvel exponencial lenta.

    signal_window : int, default=9
        Janela da média móvel exponencial do sinal.

    Retorno
    -------
    pandas.DataFrame
        DataFrame original com as colunas de MACD adicionadas.
    """

    if not isinstance(df.columns, pd.MultiIndex):
        raise ValueError("DataFrame esperado com colunas MultiIndex.")

    if df.columns.names != ["Field", "Ticker"]:
        raise ValueError(
            "Colunas MultiIndex devem estar nomeadas como ('Field', 'Ticker')."
        )

    if price_field not in df.columns.get_level_values("Field"):
        raise ValueError(f"Campo '{price_field}' não encontrado no DataFrame.")

    # Seleciona preços
    price_df = df.xs(price_field, axis=1, level="Field")

    # EMAs
    ema_fast = price_df.ewm(span=fast_window, adjust=False).mean()
    ema_slow = price_df.ewm(span=slow_window, adjust=False).mean()

    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal_window, adjust=False).mean()
    macd_hist = macd_line - signal_line

    # Reconstrói colunas MultiIndex
    macd_line.columns = pd.MultiIndex.from_product(
        [[f"MACD_{fast_window}_{slow_window}"], macd_line.columns],
        names=["Field", "Ticker"]
    )

    signal_line.columns = pd.MultiIndex.from_product(
        [[f"MACD_SIGNAL_{signal_window}"], signal_line.columns],
        names=["Field", "Ticker"]
    )

    macd_hist.columns = pd.MultiIndex.from_product(
        [[f"MACD_HIST_{fast_window}_{slow_window}_{signal_window}"], macd_hist.columns],
        names=["Field", "Ticker"]
    )

    return pd.concat(
        [df, macd_line, signal_line, macd_hist],
        axis=1
    )