"""
bollinger.py

Funções para cálculo das Bandas de Bollinger sem dependências externas.

Implementação baseada exclusivamente em pandas e numpy,
utilizando operações vetorizadas para melhor desempenho
e previsibilidade.
"""

from typing import Union
import pandas as pd

def calculate_bollinger_bands(
    df: pd.DataFrame,
    price_field: str = "Adj Close",
    window: int = 20,
    num_std: float = 2.0,
    min_periods: int | None = None
) -> pd.DataFrame:
    """
    Calcula as Bandas de Bollinger para múltiplos ativos a partir de um
    DataFrame com colunas MultiIndex (Field, Ticker).

    As bandas são calculadas de forma vetorial para todos os ativos,
    respeitando o padrão único de colunas do projeto.

    Bandas calculadas:
    - Banda média (SMA)
    - Banda superior
    - Banda inferior

    Parâmetros
    ----------
    df : pandas.DataFrame
        DataFrame com dados de mercado em formato MultiIndex.

    price_field : str, default="Adj Close"
        Campo de preço utilizado no cálculo.

    window : int, default=20
        Janela da média móvel e do desvio padrão.

    num_std : float, default=2.0
        Número de desvios padrão para as bandas superior e inferior.

    min_periods : int ou None, default=None
        Número mínimo de observações para cálculo.
        Se None, assume o mesmo valor de `window`.

    Retorno
    -------
    pandas.DataFrame
        DataFrame original com as seguintes colunas adicionadas:

        - ('BB_MID_<window>', <Ticker>)
        - ('BB_UPPER_<window>', <Ticker>)
        - ('BB_LOWER_<window>', <Ticker>)
    """

    if not isinstance(df.columns, pd.MultiIndex):
        raise ValueError("DataFrame esperado com colunas MultiIndex (Field, Ticker).")

    if price_field not in df.columns.get_level_values("Field"):
        raise ValueError(f"Campo '{price_field}' não encontrado no DataFrame.")

    if min_periods is None:
        min_periods = window

    # Seleciona preços
    price_df = df.xs(price_field, axis=1, level="Field")

    # Média móvel (banda central)
    rolling = price_df.rolling(window=window, min_periods=min_periods)
    mid_band = rolling.mean()

    # Desvio padrão
    std = rolling.std()

    upper_band = mid_band + num_std * std
    lower_band = mid_band - num_std * std

    # Reconstrução das colunas MultiIndex
    mid_band.columns = pd.MultiIndex.from_product(
        [[f"BB_MID_{window}"], mid_band.columns],
        names=["Field", "Ticker"]
    )

    upper_band.columns = pd.MultiIndex.from_product(
        [[f"BB_UPPER_{window}"], upper_band.columns],
        names=["Field", "Ticker"]
    )

    lower_band.columns = pd.MultiIndex.from_product(
        [[f"BB_LOWER_{window}"], lower_band.columns],
        names=["Field", "Ticker"]
    )

    return pd.concat(
        [df, mid_band, upper_band, lower_band],
        axis=1
    )