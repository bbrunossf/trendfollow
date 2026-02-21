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

#regra de ouro: aqui nenhuma função deve receber dataframe multiindex

def calculate_relative_strength(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula o score de Força Relativa (FR) de cada ativo, preservando
    integralmente a estrutura tabular recebida.

    CONTRATO DA FUNÇÃO
    ------------------
    - Esta função NÃO recebe DataFrames com MultiIndex.
    - O DataFrame deve estar em formato flat, com:
        index  -> ticker
        columns -> p0, p1, ..., pN (preços históricos ordenados
                   do mais antigo para o mais recente)
                   + quaisquer outras colunas auxiliares.
    - A função apenas adiciona a coluna 'FR'.

    LÓGICA DO CÁLCULO
    -----------------
    A Força Relativa é calculada a partir das variações percentuais
    entre cada preço histórico e o preço mais recente (pN),
    ponderadas pela raiz quadrada da distância temporal.

    Para N preços:
        var_i = (p_i / p_N) - 1
        peso_i = sqrt(N - i)

    FR = soma(var_i * peso_i) / soma(peso_i)

    Essa lógica é equivalente à função original baseada em
    colunas posicionais, porém agora generalizada e vetorizada.

    ERROS
    -----
    - Lança ValueError se:
        - DataFrame estiver vazio
        - índice não for único
        - menos de 2 colunas de preço (p*)
    """

    # ------------------------------------------------------------------
    # Validações estruturais
    # ------------------------------------------------------------------
    if df is None or df.empty:
        raise ValueError("DataFrame vazio recebido em calculate_relative_strength")

    if not df.index.is_unique:
        raise ValueError("Índice do DataFrame deve ser único (ticker)")

    # Identifica colunas de preço (prefixo 'p')
    price_cols = [c for c in df.columns if c.startswith("p")]

    if len(price_cols) < 2:
        raise ValueError(
            "São necessárias ao menos duas colunas de preço (p0, p1, ...)"
        )

    # Garante ordenação correta das colunas de preço
    price_cols = sorted(
        price_cols,
        key=lambda x: int(x.replace("p", ""))
    )

    # ------------------------------------------------------------------
    # Extração da matriz de preços
    # ------------------------------------------------------------------
    prices = df[price_cols]

    # Preço mais recente (última coluna)
    p_last = prices.iloc[:, -1]

    # ------------------------------------------------------------------
    # Cálculo vetorial das variações
    # ------------------------------------------------------------------
    variations = prices.div(p_last, axis=0) - 1.0

    # Remove a última coluna (variação zero contra ela mesma)
    variations = variations.iloc[:, :-1]

    # ------------------------------------------------------------------
    # Pesos temporais (raiz quadrada)
    # ------------------------------------------------------------------
    n_periods = variations.shape[1]

    weights = np.sqrt(
        np.arange(n_periods, 0, -1)
    )

    # Normalização dos pesos
    weights = weights / weights.sum()

    # ------------------------------------------------------------------
    # Cálculo do FR
    # ------------------------------------------------------------------
    fr_values = variations.mul(weights, axis=1).sum(axis=1)

    # ------------------------------------------------------------------
    # Inserção do resultado preservando o DataFrame original
    # ------------------------------------------------------------------
    df_out = df.copy()
    df_out["FR"] = fr_values.round(6)

    return df_out