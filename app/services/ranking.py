"""
Responsável por ordenar, filtrar e estruturar os ativos pontuados.

Esta camada NÃO calcula indicadores.
Ela apenas transforma scores (ex: Força Relativa) em ranking consumível
por pipeline, API e frontend.
"""

from typing import List, Dict
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


def build_ranking(df: pd.DataFrame,
                  score_column: str = "FR",
                  min_score: float = 0.0,
                  top_n: int = 20,
                  payload_fields: List[str] | None = None) -> dict:
    """
    Função de alto nível para gerar ranking completo.

    Retorna DataFrame + payload serializável.

    Parâmetros
    ----------
    df : pd.DataFrame
        DataFrame com ativos pontuados.
    score_column : str
        Coluna de score.
    min_score : float
        Score mínimo.
    top_n : int
        Quantidade máxima de ativos.
    payload_fields : list[str] | None
        Campos incluídos no payload.

    Retorno
    -------
    dict
        {
            "dataframe": pd.DataFrame,
            "payload": list[dict]
        }
    """

    ranked_df = rank_assets(df=df,
                            score_column=score_column,
                            min_score=min_score,
                            top_n=top_n)

    payload = ranking_to_payload(ranked_df, fields=payload_fields)

    return {"dataframe": ranked_df, "payload": payload}
