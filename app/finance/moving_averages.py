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

from typing import Union
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
        column: str,
        window: int = 20,
        min_periods: Union[int, None] = None,
        output_column: Union[str, None] = None) -> pd.DataFrame:
    """
    Adiciona uma média móvel simples (SMA) a uma série temporal específica
    dentro de um DataFrame.

    Uso típico:
    - Gráficos de velas
    - Indicadores técnicos
    - Análise individual de ativos

    Parâmetros
    ----------
    df : pandas.DataFrame
        DataFrame contendo a série temporal (ex.: OHLCV).

    column : str
        Nome da coluna sobre a qual a média móvel será calculada
        (ex.: 'Close').

    window : int, default=20
        Tamanho da janela da média móvel.

    min_periods : int ou None, default=None
        Número mínimo de observações na janela para calcular a média.
        Se None, assume o mesmo valor de `window`.

    output_column : str ou None, default=None
        Nome da coluna de saída.
        Se None, o nome será gerado automaticamente no formato:
        'SMA_<window>'.

    Retorno
    -------
    pandas.DataFrame
        Novo DataFrame com a coluna da média móvel adicionada.

    Exemplo de coluna criada
    ------------------------
    SMA_20
    """
    if column not in df.columns:
        raise ValueError(f"Coluna '{column}' não encontrada no DataFrame.")

    if min_periods is None:
        min_periods = window

    if output_column is None:
        output_column = f"SMA_{window}"

    df_out = df.copy()
    df_out[output_column] = (df_out[column].rolling(
        window=window, min_periods=min_periods).mean())

    return df_out
