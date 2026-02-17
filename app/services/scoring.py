"""
scoring.py

Camada responsável pelo cálculo de métricas de pontuação (scores)
dos ativos, com foco na Força Relativa (FR).

Este módulo contém apenas lógica matemática e estatística.
Não realiza ordenação, filtros finais, IO, visualização ou decisões
de alocação.
"""

from __future__ import annotations

import pandas as pd
import numpy as np


def calculate_relative_strength(
    df: pd.DataFrame,
    price_columns: list[str],
    score_column: str = "FR",
    normalize: bool = True,
    scale: tuple[float, float] = (0, 100)) -> pd.DataFrame:
    """
    Calcula a Força Relativa (FR) de cada ativo com base no desempenho
    acumulado em um conjunto de datas (ex.: últimos 6 meses).

    A lógica assume que cada linha representa um ativo e que as colunas
    de preços representam snapshots temporais ordenados do mais antigo
    para o mais recente.

    Definição básica da FR:
        FR_bruta = (Preço_final / Preço_inicial) - 1

    Opcionalmente, a FR pode ser normalizada para uma escala fixa
    (ex.: 0–100), facilitando ranking e visualização.

    Parâmetros
    ----------
    df : pandas.DataFrame
        DataFrame contendo uma linha por ativo.

    price_columns : list[str]
        Lista ordenada das colunas de preço (do período mais antigo
        para o mais recente).

    score_column : str, default="FR"
        Nome da coluna onde a Força Relativa será armazenada.

    normalize : bool, default=True
        Se True, normaliza a FR para a escala definida em `scale`.

    scale : tuple[float, float], default=(0, 100)
        Intervalo da normalização (min, max).

    Retorno
    -------
    pandas.DataFrame
        DataFrame com a coluna de Força Relativa adicionada.

    Observações
    -----------
    - Ativos com valores ausentes nos preços iniciais ou finais
      são descartados.
    - A função não realiza ordenação ou seleção de ativos.
    """
    if not price_columns:
        raise ValueError("A lista de colunas de preço está vazia.")

    missing_cols = set(price_columns) - set(df.columns)
    if missing_cols:
        raise ValueError(
            f"Colunas de preço ausentes no DataFrame: {missing_cols}")

    df_out = df.copy()

    first_col = price_columns[0]
    last_col = price_columns[-1]

    # Remove ativos sem dados suficientes
    df_out = df_out.dropna(subset=[first_col, last_col])

    # Cálculo da Força Relativa bruta
    fr_raw = (df_out[last_col] / df_out[first_col]) - 1.0

    if normalize:
        min_val, max_val = scale

        fr_min = fr_raw.min()
        fr_max = fr_raw.max()

        # Evita divisão por zero em casos degenerados
        if np.isclose(fr_min, fr_max):
            fr_scaled = pd.Series(np.full(len(fr_raw),
                                          (min_val + max_val) / 2),
                                  index=fr_raw.index)
        else:
            fr_scaled = ((fr_raw - fr_min) /
                         (fr_max - fr_min)) * (max_val - min_val) + min_val

        df_out[score_column] = fr_scaled.round(2)

    else:
        df_out[score_column] = fr_raw.round(4)

    return df_out
