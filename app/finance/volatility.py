"""
volatility.py

Cálculo de métricas de volatilidade, com foco no ATR (Average True Range),
utilizando apenas pandas e operações vetorizadas.

O módulo não contém nenhuma lógica de visualização ou decisão de trade.
"""

import pandas as pd


def atr(df: pd.DataFrame,
        high_col: str = "High",
        low_col: str = "Low",
        close_col: str = "Close",
        window: int = 14,
        prefix: str = "") -> pd.DataFrame:
    """
    Calcula o Average True Range (ATR).

    O ATR mede a volatilidade do ativo considerando gaps entre períodos.
    O cálculo segue a definição clássica de Wilder, utilizando média
    móvel exponencial.

    Parâmetros
    ----------
    df : pandas.DataFrame
        DataFrame contendo colunas de High, Low e Close.

    high_col : str, default="High"
        Nome da coluna de máxima.

    low_col : str, default="Low"
        Nome da coluna de mínima.

    close_col : str, default="Close"
        Nome da coluna de fechamento.

    window : int, default=14
        Período do ATR.

    prefix : str, default=""
        Prefixo opcional para evitar colisão de nomes.

    Retorno
    -------
    pandas.DataFrame
        Novo DataFrame com a coluna:
        - '<prefix>atr'

    Observações
    -----------
    - O DataFrame original não é modificado.
    - O primeiro valor de ATR será NaN.
    """
    required_cols = {high_col, low_col, close_col}
    missing = required_cols - set(df.columns)

    if missing:
        raise ValueError(f"Colunas ausentes no DataFrame: {missing}")

    df_out = df.copy()

    high = df_out[high_col]
    low = df_out[low_col]
    close = df_out[close_col]
    prev_close = close.shift(1)

    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ],
                   axis=1).max(axis=1)

    atr_series = tr.ewm(alpha=1 / window, adjust=False).mean()

    df_out[f"{prefix}atr"] = atr_series

    return df_out


def atr_stop(df: pd.DataFrame,
             close_col: str = "Close",
             atr_col: str = "atr",
             multiplier: float = 1.5,
             column_name: str = "atr_stop") -> pd.DataFrame:
    """
    Calcula o nível de stop baseado no ATR.

    A regra aplicada é:
        Stop = Close - (ATR × multiplicador)

    Parâmetros
    ----------
    df : pandas.DataFrame
        DataFrame contendo o preço de fechamento e o ATR.

    close_col : str, default="Close"
        Nome da coluna de fechamento.

    atr_col : str, default="atr"
        Nome da coluna de ATR.

    multiplier : float, default=1.5
        Fator multiplicador do ATR.

    column_name : str, default="atr_stop"
        Nome da coluna gerada.

    Retorno
    -------
    pandas.DataFrame
        Novo DataFrame com a coluna de stop ATR adicionada.

    Observações
    -----------
    - A função não valida lógica de compra/venda.
    - O stop é apenas um nível técnico derivado da volatilidade.
    """
    if close_col not in df.columns:
        raise ValueError(f"Coluna '{close_col}' não encontrada no DataFrame.")

    if atr_col not in df.columns:
        raise ValueError(f"Coluna '{atr_col}' não encontrada no DataFrame.")

    df_out = df.copy()

    df_out[column_name] = df_out[close_col] - (df_out[atr_col] * multiplier)

    return df_out
