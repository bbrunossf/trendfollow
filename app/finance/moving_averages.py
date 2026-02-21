"""
moving_averages.py

Funções utilitárias para cálculo de médias móveis em séries financeiras.

Este módulo separa explicitamente dois conceitos diferentes de média móvel:

1) Médias móveis aplicadas a DataFrames matriciais (datas x ativos),
   normalmente usadas em rankings, filtros e scores cross-sectionais.

2) Médias móveis aplicadas a séries temporais individuais,
   normalmente usadas em visualizações e indicadores técnicos.

Essa separação é intencional e evita ambiguidades no pipeline de dados.
"""

from typing import Union, Iterable
import pandas as pd


def moving_average_matrix(
        df: pd.DataFrame,
        window: int = 20,
        min_periods: Union[int, None] = None) -> pd.DataFrame:
    """
    Calcula a média móvel simples (SMA) para um DataFrame matricial.

    Cada coluna é tratada como uma série temporal independente
    (ex.: preços de fechamento de diferentes ativos),
    e a média móvel é calculada ao longo do índice (datas).

    Uso típico:
    - Ranking de ativos
    - Cálculo de scores (ex.: FR)
    - Filtros cross-sectionais

    Parâmetros
    ----------
    df : pandas.DataFrame
        DataFrame onde:
        - o índice representa datas
        - cada coluna representa um ativo
        - os valores são preços ou séries numéricas

    window : int, default=20
        Tamanho da janela da média móvel.

    min_periods : int ou None, default=None
        Número mínimo de observações na janela para calcular a média.
        Se None, assume o mesmo valor de `window`.

    Retorno
    -------
    pandas.DataFrame
        Novo DataFrame contendo as médias móveis,
        com a mesma estrutura (índice e colunas) do DataFrame original.

    Observações
    -----------
    - A função NÃO modifica o DataFrame original.
    - Valores iniciais podem conter NaN, dependendo de `min_periods`.
    """
    if min_periods is None:
        min_periods = window

    return df.rolling(window=window, min_periods=min_periods).mean()


def simple_moving_average(
    df: pd.DataFrame,
    price_field: str = "Adj Close",
    window: int = 20,
    min_periods: int | None = None
) -> pd.DataFrame:
    """
    Calcula a Média Móvel Simples (SMA) para múltiplos ativos a partir de um
    DataFrame com colunas MultiIndex (Field, Ticker).

    Esta função assume que o DataFrame segue o padrão:
        - Index: DatetimeIndex
        - Columns: MultiIndex com níveis ['Field', 'Ticker']

    A SMA será calculada de forma vetorial para todos os tickers e adicionada
    ao DataFrame no mesmo padrão MultiIndex.

    Parâmetros
    ----------
    df : pandas.DataFrame
        DataFrame com dados OHLCV em formato MultiIndex.

    price_field : str, default="Adj Close"
        Campo de preço utilizado para o cálculo da média móvel
        (ex.: 'Close', 'Adj Close').

    window : int, default=20
        Tamanho da janela da média móvel.

    min_periods : int ou None, default=None
        Número mínimo de observações para cálculo da média.
        Se None, assume o mesmo valor de `window`.

    Retorno
    -------
    pandas.DataFrame
        Novo DataFrame com a coluna de SMA adicionada no formato:
        ('SMA_<window>', <Ticker>)

    Exemplo de coluna criada
    ------------------------
    ('SMA_20', 'PETR4.SA')
    """

    if not isinstance(df.columns, pd.MultiIndex):
        raise ValueError("DataFrame esperado com colunas MultiIndex (Field, Ticker).")

    if price_field not in df.columns.get_level_values("Field"):
        raise ValueError(f"Campo '{price_field}' não encontrado no DataFrame.")

    if min_periods is None:
        min_periods = window

    # Seleciona apenas o campo de preço (ex.: Close)
    price_df = df.xs(price_field, axis=1, level="Field")

    # Cálculo vetorial da média móvel para todos os tickers
    sma_df = price_df.rolling(
        window=window,
        min_periods=min_periods
    ).mean()

    # Reconstrói o MultiIndex das colunas
    sma_df.columns = pd.MultiIndex.from_product(
        [[f"SMA_{window}"], sma_df.columns],
        names=["Field", "Ticker"]
    )

    # Retorna um novo DataFrame com a SMA anexada
    return pd.concat([df, sma_df], axis=1)

