"""
bollinger.py

Funções para cálculo das Bandas de Bollinger sem dependências externas.

Implementação baseada exclusivamente em pandas e numpy,
utilizando operações vetorizadas para melhor desempenho
e previsibilidade.
"""

from typing import Union
import pandas as pd


def bollinger_bands(df: pd.DataFrame,
                    column: str,
                    window: int = 20,
                    num_std: float = 2.0,
                    min_periods: Union[int, None] = None,
                    prefix: str = "") -> pd.DataFrame:
    """
    Calcula as Bandas de Bollinger para uma série temporal específica.

    As bandas são calculadas como:
    - SMA (média móvel simples)
    - Banda superior: SMA + (num_std * desvio padrão)
    - Banda inferior: SMA - (num_std * desvio padrão)

    Uso típico:
    - Visualização em gráficos de velas
    - Análise de volatilidade
    - Indicadores técnicos clássicos

    Parâmetros
    ----------
    df : pandas.DataFrame
        DataFrame contendo a série temporal (ex.: OHLCV).

    column : str
        Nome da coluna sobre a qual as Bandas de Bollinger serão calculadas
        (ex.: 'Close').

    window : int, default=20
        Tamanho da janela da média móvel e do desvio padrão.

    num_std : float, default=2.0
        Número de desvios padrão usados para definir
        as bandas superior e inferior.

    min_periods : int ou None, default=None
        Número mínimo de observações na janela para calcular os valores.
        Se None, assume o mesmo valor de `window`.

    prefix : str, default=""
        Prefixo opcional para os nomes das colunas geradas.
        Útil caso múltiplas bandas sejam calculadas no mesmo DataFrame.

    Retorno
    -------
    pandas.DataFrame
        Novo DataFrame com as seguintes colunas adicionadas:
        - '<prefix>sma'
        - '<prefix>upper_band'
        - '<prefix>lower_band'

    Observações
    -----------
    - A função NÃO modifica o DataFrame original.
    - O cálculo é totalmente vetorizado.
    """
    if column not in df.columns:
        raise ValueError(f"Coluna '{column}' não encontrada no DataFrame.")

    if min_periods is None:
        min_periods = window

    df_out = df.copy()

    rolling = df_out[column].rolling(window=window, min_periods=min_periods)

    sma = rolling.mean()
    std = rolling.std()

    df_out[f"{prefix}sma"] = sma
    df_out[f"{prefix}upper_band"] = sma + (num_std * std)
    df_out[f"{prefix}lower_band"] = sma - (num_std * std)

    return df_out
