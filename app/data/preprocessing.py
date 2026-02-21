from typing import Dict, Any, Optional, List
import pandas as pd

def resolve_to_trading_dates(
    index: pd.DatetimeIndex,
    theoretical_dates: list[pd.Timestamp]
) -> list[pd.Timestamp]:
    """
    Para cada data teórica, encontra o último pregão disponível
    anterior ou igual à data.
    """
    resolved = []

    for d in theoretical_dates:
        valid_dates = index[index <= d]
        if valid_dates.empty:
            raise ValueError(
                f"Não há dados de mercado antes de {d.date()}"
            )
        resolved.append(valid_dates.max())

    return resolved

def extract_price_snapshots(
    prices: pd.DataFrame,
    trading_dates: list[pd.Timestamp],
    price_field: str = "Adj Close"
) -> pd.DataFrame:
    """
    Extrai snapshots de preço para datas específicas,
    assumindo colunas MultiIndex (Field, Ticker).
    """
    return prices.loc[
        trading_dates,
        prices.columns.get_level_values("Field") == price_field
    ]

def flatten_snapshot_for_scoring(
    snapshot: pd.DataFrame,
    price_field: str = "Adj Close",
    prefix: str = "p"
) -> pd.DataFrame:
    """
    Converte um snapshot histórico MultiIndex em um DataFrame tabular
    (flat) adequado para cálculo de Força Relativa (FR).

    A função reorganiza os dados de forma que:
    - cada linha represente um ativo (ticker)
    - cada coluna represente um preço em uma data distinta
    - as datas sejam ordenadas do período mais antigo para o mais recente

    CONTRATO DA FUNÇÃO
    ------------------
    - Esta função RECEBE um DataFrame com:
        index : DatetimeIndex (múltiplas datas)
        columns : MultiIndex com níveis ['Field', 'Ticker']
    - Esta função DEVOLVE um DataFrame com:
        index : ticker
        columns : colunas simples (Index plano), contendo preços históricos

    A função NÃO:
    - calcula Força Relativa
    - normaliza dados
    - remove ativos com NaN
    - adiciona indicadores técnicos
    - faz merges ou joins

    PARÂMETROS
    ----------
    snapshot : pandas.DataFrame
        DataFrame MultiIndex contendo múltiplas datas e ativos.

    price_field : str, default="Adj Close"
        Nome do campo de preço a ser utilizado no cálculo de FR.

    prefix : str, default="p"
        Prefixo usado para nomear as colunas de preço (ex.: p0, p1, p2...).

    RETORNO
    -------
    pandas.DataFrame
        DataFrame flat com:
            - índice: ticker
            - colunas: preços históricos ordenados temporalmente

        Exemplo de colunas:
            p0, p1, p2, ..., pN

    ERROS
    -----
    ValueError se:
        - snapshot estiver vazio
        - snapshot não tiver MultiIndex nas colunas
        - price_field não existir no nível 'Field'
        - snapshot contiver menos de duas datas
    """

    # ------------------------------------------------------------------
    # Validações estruturais
    # ------------------------------------------------------------------
    if snapshot is None or snapshot.empty:
        raise ValueError("Snapshot vazio recebido em flatten_snapshot_for_scoring")

    if not isinstance(snapshot.columns, pd.MultiIndex):
        raise ValueError("Snapshot deve possuir colunas MultiIndex")

    if "Field" not in snapshot.columns.names or "Ticker" not in snapshot.columns.names:
        raise ValueError("Snapshot deve ter níveis de coluna ['Field', 'Ticker']")

    if price_field not in snapshot.columns.get_level_values("Field"):
        raise ValueError(f"Campo de preço '{price_field}' não encontrado no snapshot")

    if snapshot.shape[0] < 2:
        raise ValueError("Snapshot deve conter ao menos duas datas para cálculo de FR")

    # ------------------------------------------------------------------
    # Seleção do campo de preço
    # ------------------------------------------------------------------
    prices = snapshot.loc[:, price_field]

    # prices:
    # index  -> Date
    # columns -> Ticker

    # ------------------------------------------------------------------
    # Ordenação temporal explícita
    # ------------------------------------------------------------------
    prices = prices.sort_index()

    # ------------------------------------------------------------------
    # Reorganização: datas viram colunas
    # ------------------------------------------------------------------
    prices_t = prices.T

    # prices_t:
    # index   -> Ticker
    # columns -> Date

    # ------------------------------------------------------------------
    # Renomeação das colunas (datas -> p0, p1, ..., pN)
    # ------------------------------------------------------------------
    new_columns = {
        date: f"{prefix}{i}"
        for i, date in enumerate(prices_t.columns)
    }

    prices_t = prices_t.rename(columns=new_columns)

    # ------------------------------------------------------------------
    # Garantias finais
    # ------------------------------------------------------------------
    prices_t.index.name = "ticker"

    return prices_t

def build_price_matrix_for_chart(
    price_snapshots: pd.DataFrame,
    selected_tickers: list[str],
    price_field: str = "Adj Close",
) -> pd.DataFrame:
    """
    Constrói o DataFrame de entrada para o gráfico de validação do FR.

    A função recebe um snapshot de preços em formato MultiIndex
    (Field, Ticker) x Date e retorna uma matriz tabular simples,
    com uma linha por ativo e uma coluna por data.

    Parâmetros
    ----------
    price_snapshots : pandas.DataFrame
        DataFrame MultiIndex com:
        - index: datas (datetime)
        - columns: MultiIndex ['Field', 'Ticker']

    selected_tickers : list[str]
        Lista de tickers selecionados (ex.: FR_rank >= min_score).

    price_field : str, default="Adj Close"
        Campo de preço a ser utilizado.

    Retorno
    -------
    pandas.DataFrame
        DataFrame com:
        - index: ticker
        - columns: datas (ordenadas, datetime)
        - valores: preços ajustados
    """

    if price_snapshots.empty:
        raise ValueError("price_snapshots está vazio")

    if not selected_tickers:
        raise ValueError("Lista de tickers selecionados está vazia")

    if not isinstance(price_snapshots.columns, pd.MultiIndex):
        raise ValueError("price_snapshots deve possuir colunas MultiIndex")

    if "Field" not in price_snapshots.columns.names:
        raise ValueError("Nível 'Field' não encontrado nas colunas")

    if "Ticker" not in price_snapshots.columns.names:
        raise ValueError("Nível 'Ticker' não encontrado nas colunas")

    # ------------------------------------------------------------------
    # 1. Seleciona apenas o campo de preço desejado
    # ------------------------------------------------------------------
    try:
        prices_field = price_snapshots.loc[:, price_field]
    except KeyError as exc:
        raise ValueError(
            f"Campo de preço '{price_field}' não encontrado no snapshot"
        ) from exc

    # prices_field:
    # index  -> Date
    # columns -> Ticker

    # ------------------------------------------------------------------
    # 2. Filtra apenas os tickers selecionados
    # ------------------------------------------------------------------
    missing = set(selected_tickers) - set(prices_field.columns)
    if missing:
        raise ValueError(
            f"Tickers ausentes no snapshot de preços: {missing}"
        )

    prices_filtered = prices_field[selected_tickers]

    # ------------------------------------------------------------------
    # 3. Reorganiza para formato final (ticker x datas)
    # ------------------------------------------------------------------
    df_chart = prices_filtered.T

    # Garante ordenação temporal das colunas
    df_chart = df_chart.sort_index(axis=1)

    # ------------------------------------------------------------------
    # 4. Valida estrutura final
    # ------------------------------------------------------------------
    if not df_chart.index.is_unique:
        raise ValueError("Índice final (ticker) não é único")

    if df_chart.empty:
        raise ValueError("DataFrame final do gráfico está vazio")

    return df_chart


def build_plotly_price_dataframe(
    price_snapshots: pd.DataFrame,
    ranking_payload: list[dict],
    price_field: str = "Adj Close"
) -> pd.DataFrame:
    """
    Constrói o DataFrame final para visualização no Plotly.

    Retorna um DataFrame em formato longo (long-form), contendo:
    - ticker
    - date
    - adj_close
    - variação percentual ponto-a-ponto
    - FR
    - FR_rank
    """

    if price_snapshots.empty:
        raise ValueError("price_snapshots vazio")

    if not ranking_payload:
        raise ValueError("ranking_payload vazio")

    # ------------------------------------------------------------------
    # 1. Ativos selecionados no ranking
    # ------------------------------------------------------------------
    ranking_df = pd.DataFrame(ranking_payload)[["ticker", "FR", "FR_rank"]]
    selected_tickers = ranking_df["ticker"].tolist()

    # ------------------------------------------------------------------
    # 2. Extrair apenas Adj Close dos ativos selecionados
    # ------------------------------------------------------------------
    adj_close = (
        price_snapshots
        .loc[:, (price_field, selected_tickers)]
        .copy()
    )

    # ------------------------------------------------------------------
    # 3. Flatten: Date vira coluna, ticker vira coluna
    # ------------------------------------------------------------------
    adj_close.columns = adj_close.columns.droplevel(0)
    adj_close = adj_close.reset_index()  # Date vira coluna

    long_df = adj_close.melt(
        id_vars="Date",
        var_name="ticker",
        value_name="adj_close"
    )

    # ------------------------------------------------------------------
    # 4. Ordenação temporal e cálculo da variação percentual
    # ------------------------------------------------------------------
    long_df = long_df.sort_values(["ticker", "Date"])

    long_df["pct_change"] = (
        long_df
        .groupby("ticker")["adj_close"]
        .pct_change()
        .mul(100)
    )

    # ------------------------------------------------------------------
    # 5. Enriquecimento com FR e FR_rank
    # ------------------------------------------------------------------
    long_df = long_df.merge(
        ranking_df,
        on="ticker",
        how="left"
    )

    return long_df
    
    
    
def add_percent_change_for_hover(
    df_prices: pd.DataFrame,
    prefix: str = "pct_"
) -> pd.DataFrame:
    """
    Adiciona colunas de variação percentual ponto-a-ponto para uso em hover.

    Parâmetros
    ----------
    df_prices : pd.DataFrame
        DataFrame com:
        - índice = ticker
        - colunas = datas (ordenadas cronologicamente)
        - valores = preços ajustados (Adj Close)

    prefix : str
        Prefixo das colunas de variação percentual.

    Retorno
    -------
    pd.DataFrame
        Mesmo DataFrame, com colunas adicionais no formato:
        pct_<data>
    """

    if df_prices.empty:
        raise ValueError("DataFrame vazio")

    # garantir ordenação temporal das colunas
    df_prices = df_prices.copy()
    df_prices = df_prices.sort_index(axis=1)

    pct_change = df_prices.pct_change(axis=1) * 100
    pct_change.columns = [f"{prefix}{col}" for col in pct_change.columns]

    return pd.concat([df_prices, pct_change], axis=1)
    
def build_plotly_payload(df_chart: pd.DataFrame) -> list[dict]:
    """
    Constrói o payload JSON para consumo direto pelo Plotly JS.

    Retorna uma lista de traces, um por ativo.
    """

    payload = []

    for ticker, row in df_chart.iterrows():
        prices = row.values
        dates = df_chart.columns.astype(str).tolist()

        # Variação percentual em relação ao primeiro ponto
        base_price = prices[0]
        pct_change = ((prices / base_price) - 1.0) * 100

        trace = {
            "type": "scatter",
            "mode": "lines+markers",
            "name": ticker,
            "x": dates,
            "y": prices.tolist(),
            "customdata": pct_change.round(2).tolist(),
            "hovertemplate": (
                "<b>%{fullData.name}</b><br>"
                "Data: %{x}<br>"
                "Preço: %{y:.2f}<br>"
                "Variação: %{customdata:.2f}%"
                "<extra></extra>"
            ),
        }

        payload.append(trace)

    return payload


def extract_latest(prices: pd.DataFrame,
                   price_field: str = "Adj Close",
                   indicator_fields: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Extrai o último registro por ticker a partir do DataFrame 'prices' que tem
    MultiIndex nas colunas com níveis ['Field','Ticker'].
    Retorna DataFrame com colunas: ['Ticker', price_field, <indicator_fields>].
    """
    if not isinstance(prices.columns, pd.MultiIndex):
        raise ValueError("extract_latest: espera columns como MultiIndex com níveis ['Field','Ticker'].")

    # lista de fields disponíveis e tickers (garantir strings)
    fields_available = list(prices.columns.get_level_values('Field').unique())
    tickers = prices.columns.get_level_values('Ticker').unique().astype(str)

    # detectar STOP_ATR se indicator_fields não fornecido
    if indicator_fields is None:
        indicator_fields = [f for f in fields_available if str(f).upper().startswith("STOP_ATR")]
    else:
        # filtrar somente os que existem
        indicator_fields = [f for f in indicator_fields if f in fields_available]

    needed_fields = [price_field] + indicator_fields

    series_list = []
    for fld in needed_fields:
        if fld in fields_available:
            df_field = prices.xs(fld, axis=1, level='Field')
            # garantir DataFrame (caso particular)
            if isinstance(df_field, pd.Series):
                df_field = df_field.to_frame().T

            # se não houver linhas (por algum motivo), criar Series de NaNs
            if df_field.shape[0] == 0:
                s = pd.Series(index=tickers, data=np.nan, name=str(fld))
            else:
                s = df_field.iloc[-1]                # último candle
                # garantir que o índice seja string e correspondente a 'tickers'
                s.index = s.index.astype(str)
                s = s.reindex(tickers)              # alinha na mesma ordem / mesmo índice
                s.name = str(fld)
        else:
            # field ausente -> série de NaNs
            s = pd.Series(index=tickers, data=np.nan, name=str(fld))

        series_list.append(s)

    # concatenar séries (todas com mesmo índice: tickers)
    df_latest = pd.concat(series_list, axis=1)
    df_latest.index.name = 'Ticker'
    df_latest = df_latest.reset_index()  # torna 'Ticker' coluna
    return df_latest