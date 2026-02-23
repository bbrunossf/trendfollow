from typing import Dict
import pandas as pd


class PriceRepository:
    """
    Repositório em memória para armazenar históricos de preços (`prices`)
    indexados pela data de referência.

    Responsabilidades:
    - armazenar DataFrames em memória
    - recuperar DataFrames por reference_date
    - informar se um histórico já existe

    Escopo:
    - memória do processo (1 worker)
    - dados voláteis (descartados ao reiniciar a aplicação)
    """

    def __init__(self) -> None:
        self._store: Dict[str, pd.DataFrame] = {}
        self._current_reference_date: str | None = None

    def has(self, reference_date: str) -> bool:
        """
        Verifica se existe histórico de preços para a data de referência.
        """
        return reference_date in self._store

    def get(self, reference_date: str) -> pd.DataFrame:
        """
        Recupera o histórico de preços associado à data de referência.

        Levanta KeyError se não existir.
        """
        if reference_date not in self._store:
            raise KeyError(
                f"Prices não encontrado para reference_date={reference_date}"
            )
        return self._store[reference_date]

    def set(self, reference_date: str, prices: pd.DataFrame) -> None:
        """
        Armazena (ou sobrescreve) o histórico de preços para a data de referência.
        """
        if not isinstance(prices, pd.DataFrame):
            raise TypeError("prices deve ser um pandas.DataFrame")

        self._store[reference_date] = prices
        self._current_reference_date = reference_date
    
    def current_reference_date(self) -> str:
        """
        Retorna a data de referência atualmente ativa.

        Levanta RuntimeError se nenhuma data tiver sido inicializada.
        """
        if self._current_reference_date is None:
            raise RuntimeError("Nenhuma reference_date foi inicializada ainda")
        return self._current_reference_date

    def clear(self) -> None:
        """
        Remove todos os históricos armazenados (útil para debug ou testes).
        """
        self._store.clear()
        self._current_reference_date = None


# Instância única do repositório (escopo de aplicação)
price_repository = PriceRepository()