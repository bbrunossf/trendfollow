import pandas as pd
import numpy as np


def calculate_risk_return_indicators(
    df: pd.DataFrame,
    price_col: str = "Adj Close",
    stop_col: str = "STOP_ATR_14_1.5",
    high_52w_col: str = "high_52w",
    round_decimals: int = 2,
) -> pd.DataFrame:
    """
    Calcula indicadores customizados de risco e retorno.

    Indicadores calculados:
    - distancia: diferença percentual entre o preço máximo das últimas
      52 semanas e o preço atual.
    - Risco_%: perda percentual assumida caso o ativo atinja o stop ATR.
    - Retorno_Risco: relação entre retorno potencial e risco assumido.

    Parâmetros
    ----------
    df
        DataFrame enriquecido contendo preços, stop_atr e high_52w.
    price_col
        Coluna com o preço atual (preferencialmente Adj Close).
    stop_col
        Coluna com o valor do stop baseado em ATR.
    high_52w_col
        Coluna com o preço máximo das últimas 52 semanas.
    round_decimals
        Número de casas decimais para arredondamento final.

    Retorna
    -------
    pd.DataFrame
        DataFrame com as novas colunas:
        - distancia
        - Risco_%
        - Retorno_Risco
    """

    df = df.copy()

    # ------------------------------------------------------------------
    # Distância até o topo de 52 semanas (%)
    # ------------------------------------------------------------------
    df["distancia"] = np.where(
        df[high_52w_col] > 0,
        ((df[high_52w_col] - df[price_col]) / df[high_52w_col]) * 100,
        np.nan,
    )

    # ------------------------------------------------------------------
    # Risco percentual até o stop ATR
    # ------------------------------------------------------------------
    df["Risco_%"] = np.where(
        df[stop_col] > 0,
        ((df[price_col] - df[stop_col]) / df[stop_col]) * 100,
        np.nan,
    )

    # ------------------------------------------------------------------
    # Relação Retorno / Risco
    # ------------------------------------------------------------------
    df["Retorno_Risco"] = np.where(
        df["Risco_%"] != 0,
        df["distancia"] / df["Risco_%"],
        np.nan,
    )

    # ------------------------------------------------------------------
    # Arredondamento final (apenas métricas derivadas)
    # ------------------------------------------------------------------
    cols_to_round = ["distancia", "Risco_%", "Retorno_Risco"]
    df[cols_to_round] = df[cols_to_round].round(round_decimals)

    return df
