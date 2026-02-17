"""
macd.py

Cálculo do indicador MACD (Moving Average Convergence Divergence)
utilizando apenas pandas, sem dependências externas.

O módulo é intencionalmente desacoplado de qualquer lógica de visualização.
"""

from typing import Union
import pandas as pd


def macd(df: pd.DataFrame,
         column: str,
         fast: int = 12,
         slow: int = 26,
         signal: int = 9,
         prefix: str = "") -> pd.DataFrame:
    """
    Calcula o indicador MACD (Moving Average Convergence Divergence).

    O MACD é definido como:
    - MACD line = EMA(fast) - EMA(slow)
    - Signal line = EMA(signal) da MACD line
    - Histogram = MACD line - Signal line

    Uso típico:
    - Análise de momentum
    - Gráficos técnicos
    - Estratégias de tendência

    Parâmetros
    ----------
    df : pandas.DataFrame
        DataFrame contendo a série temporal.

    column : str
        Nome da coluna base para o cálculo (ex.: 'Close').

    fast : int, default=12
        Período da média móvel exponencial rápida.

    slow : int, default=26
        Período da média móvel exponencial lenta.

    signal : int, default=9
        Período da média móvel exponencial da linha MACD.

    prefix : str, default=""
        Prefixo opcional para os nomes das colunas geradas.
        Útil para evitar colisão de nomes.

    Retorno
    -------
    pandas.DataFrame
        Novo DataFrame com as seguintes colunas adicionadas:
        - '<prefix>macd'
        - '<prefix>macd_signal'
        - '<prefix>macd_hist'

    Observações
    -----------
    - A função NÃO modifica o DataFrame original.
    - O cálculo é totalmente vetorizado.
    """
    if column not in df.columns:
        raise ValueError(f"Coluna '{column}' não encontrada no DataFrame.")

    df_out = df.copy()

    ema_fast = df_out[column].ewm(span=fast, adjust=False).mean()
    ema_slow = df_out[column].ewm(span=slow, adjust=False).mean()

    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line

    df_out[f"{prefix}macd"] = macd_line
    df_out[f"{prefix}macd_signal"] = signal_line
    df_out[f"{prefix}macd_hist"] = hist

    return df_out
