"""
ranking_repository.py

Repositório em memória para armazenar o resultado de build_ranking_result,
indexado pela data de referência.

Responsabilidades:
- armazenar o resultado completo do pipeline de ranking (dict)
- recuperar resultados por reference_date sem recomputação
- informar se um resultado já foi calculado para uma data

Escopo:
- memória do processo (1 worker)
- dados voláteis (descartados ao reiniciar a aplicação)
"""

from typing import Any, Dict


class RankingRepository:
    """
    Cache em memória dos resultados produzidos por build_ranking_result.

    Cada entrada é indexada por reference_date (str no formato YYYY-MM-DD)
    e armazena o dict completo retornado pelo pipeline de ranking, contendo:
    - "summary"         : métricas resumidas da execução
    - "ranking"         : list[dict] dos ativos ranqueados e enriquecidos
    - "price_snapshots" : pd.DataFrame com snapshots de preço por data
    """

    def __init__(self) -> None:
        self._store: Dict[str, Dict[str, Any]] = {}
        self._current_reference_date: str | None = None

    # ------------------------------------------------------------------
    # Consulta
    # ------------------------------------------------------------------

    def has(self, reference_date: str) -> bool:
        """
        Verifica se já existe um resultado calculado para a data de referência.
        """
        return reference_date in self._store

    def get(self, reference_date: str) -> Dict[str, Any]:
        """
        Recupera o resultado do pipeline associado à data de referência.

        Levanta KeyError se não existir.
        """
        if reference_date not in self._store:
            raise KeyError(
                f"Resultado de ranking não encontrado para reference_date={reference_date!r}. "
                "Chame build_ranking_result antes de acessar o repositório."
            )
        return self._store[reference_date]

    def current_reference_date(self) -> str:
        """
        Retorna a data de referência da última entrada armazenada.

        Levanta RuntimeError se nenhuma data tiver sido registrada ainda.
        """
        if self._current_reference_date is None:
            raise RuntimeError(
                "Nenhuma reference_date foi registrada no RankingRepository ainda."
            )
        return self._current_reference_date

    # ------------------------------------------------------------------
    # Escrita
    # ------------------------------------------------------------------

    def set(self, reference_date: str, result: Dict[str, Any]) -> None:
        """
        Armazena (ou sobrescreve) o resultado do pipeline para a data de referência.

        Parâmetros
        ----------
        reference_date : str
            Data de referência no formato YYYY-MM-DD.
        result : dict
            Dict retornado por build_ranking_result, contendo ao menos
            as chaves "summary", "ranking" e "price_snapshots".

        Levanta
        -------
        TypeError se result não for um dicionário.
        ValueError se result não contiver as chaves obrigatórias.
        """
        if not isinstance(result, dict):
            raise TypeError(
                f"result deve ser um dicionário, recebido: {type(result).__name__!r}"
            )

        required_keys = {"summary", "ranking", "price_snapshots"}
        missing = required_keys - result.keys()
        if missing:
            raise ValueError(f"result está incompleto. Chaves ausentes: {missing}")

        self._store[reference_date] = result
        self._current_reference_date = reference_date

    # ------------------------------------------------------------------
    # Manutenção
    # ------------------------------------------------------------------

    def clear(self) -> None:
        """
        Remove todos os resultados armazenados.
        Útil para forçar recomputação ou em testes.
        """
        self._store.clear()
        self._current_reference_date = None

    def __repr__(self) -> str:
        dates = list(self._store.keys())
        return (
            f"RankingRepository("
            f"cached_dates={dates}, "
            f"current={self._current_reference_date!r})"
        )


# Instância única do repositório (escopo de aplicação)
ranking_repository = RankingRepository()
