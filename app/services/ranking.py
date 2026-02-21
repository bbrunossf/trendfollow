"""
Responsável por ordenar, filtrar e estruturar os ativos pontuados.

Esta camada NÃO calcula indicadores.
Ela apenas transforma scores (ex: Força Relativa) em ranking consumível
por pipeline, API e frontend.
"""

from typing import List, Dict, Any
import pandas as pd


def rank_assets(df: pd.DataFrame,
                score_column: str = "FR",
                min_score: float = 0.0,
                top_n: int | None = None) -> pd.DataFrame:
    """
    Ordena os ativos com base em uma coluna de score.

    Parâmetros
    ----------
    df : pd.DataFrame
        DataFrame contendo os ativos já pontuados.
    score_column : str
        Nome da coluna que contém o score (default: 'FR').
    min_score : float
        Score mínimo para o ativo ser considerado.
    top_n : int | None
        Quantidade máxima de ativos retornados.

    Retorno
    -------
    pd.DataFrame
        DataFrame ordenado do maior para o menor score.
    """

    if score_column not in df.columns:
        raise ValueError(
            f"Coluna '{score_column}' não encontrada no DataFrame")

    ranked = (df[df[score_column] >= min_score].sort_values(
        by=score_column, ascending=False).reset_index(drop=True))

    if top_n is not None:
        ranked = ranked.head(top_n)

    return ranked


def ranking_to_payload(df: pd.DataFrame,
                       fields: List[str] | None = None) -> List[Dict]:
    """
    Converte o ranking em estrutura serializável (JSON-like).

    Parâmetros
    ----------
    df : pd.DataFrame
        DataFrame já ordenado.
    fields : list[str] | None
        Lista de campos a incluir no payload.
        Se None, inclui todas as colunas.

    Retorno
    -------
    list[dict]
        Ranking pronto para retorno em API.
    """

    if fields is not None:
        missing = set(fields) - set(df.columns)
        if missing:
            raise ValueError(f"Campos ausentes no DataFrame: {missing}")
        df = df[fields]

    return df.to_dict(orient="records")


def build_ranking(
    df: pd.DataFrame,
    score_column: str = "FR",
    min_score: float | None = None,
    top_n: int | None = None,
    payload_fields: List[str] | None = None
) -> Dict[str, Any]:
    """
    Constrói o ranking de ativos a partir de um score contínuo (ex.: FR),
    gerando adicionalmente um score ordinal percentual (FR_rank).

    CONTRATO
    --------
    - df deve ser um DataFrame flat
    - índice representa o ticker
    - score_column deve existir no DataFrame
    - a função NÃO calcula indicadores nem scores primários

    LÓGICA
    ------
    1. Ordena os ativos pelo score contínuo (descendente)
    2. Constrói FR_rank (0–100) com base na posição relativa
    3. Aplica filtros usando FR_rank
    4. Prepara payload final
    """

    # ------------------------------------------------------------------
    # Validações iniciais
    # ------------------------------------------------------------------
    #print("df recebido no build_ranking")
    #print(df)
    #print(df.columns)
    
    if df is None or df.empty:
        raise ValueError("DataFrame vazio recebido em build_ranking")

    if not df.index.is_unique:
        raise ValueError("Índice do DataFrame deve ser único (ticker)")

    if score_column not in df.columns:
        raise ValueError(f"Coluna de score '{score_column}' não encontrada")

    # ------------------------------------------------------------------
    # Trabalho sobre cópia explícita
    # ------------------------------------------------------------------
    ranked = df.copy()

    ranked = ranked[ranked[score_column].notna()]

    if ranked.empty:
        return {"ranking": ranked, "payload": []}

    # ------------------------------------------------------------------
    # Ordenação pelo score contínuo
    # ------------------------------------------------------------------
    ranked = ranked.sort_values(by=score_column, ascending=False)

    # ------------------------------------------------------------------
    # Criação do FR_rank (percentil 0–100)
    # ------------------------------------------------------------------
    ranked["FR_rank"] = (
        ranked[score_column]
        .rank(method="first", ascending=False, pct=True)
        * 100
    ).round(2)

    # ------------------------------------------------------------------
    # Filtro por FR_rank
    # ------------------------------------------------------------------
    if min_score is not None:
        ranked = ranked[ranked["FR_rank"] >= min_score]
        #print("df final")
        #print(ranked)
        #print(ranked.columns)
        #print(ranked.index)

    if ranked.empty:
        return {"ranking": ranked, "payload": []}

    # ------------------------------------------------------------------
    # Limite de quantidade
    # ------------------------------------------------------------------
    if top_n is not None:
        ranked = ranked.head(top_n)

    # ------------------------------------------------------------------
    # Construção do payload
    # ------------------------------------------------------------------
    payload = []
    fields = payload_fields or []

    for ticker, row in ranked.iterrows():
        item = {"ticker": ticker}

        for field in fields:
            if field not in ranked.columns:
                raise ValueError(
                    f"Campo '{field}' solicitado no payload não existe no DataFrame"
                )
            item[field] = row[field]

        # Scores sempre disponíveis
        item["FR"] = row[score_column]
        item["FR_rank"] = row["FR_rank"]

        payload.append(item)

    return {
        "ranking": ranked,
        "payload": payload
    }