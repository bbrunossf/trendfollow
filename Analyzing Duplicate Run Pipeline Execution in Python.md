## User

Segue abaixo um fluxo resumido de uma aplicação que estou desenvolvendo em python, com frontend usando JS bem simples. Segue também a estrutura de pastas e arquivos, e uma descrição dos principais arquivos. Estou notando que a função "run_pipeline" está sendo executada duas vezes, e me parece que isso está errado. Analise o trecho abaixo e o projetos como um todo. Faça a sugestão de desmembramento do run_pipeline para melhorar a divisão de responsabilidades e otimizar a estrutura do projeto de forma profissional

#Usuario Clica em Run -> aciona fr_chart.js.runPipeline() -> chama o endpoint /api/fr-price-series -> executa a função init.init -> lista os ativos filtrando por volume e preço, -> executa o run_pipeline (ajusta as datas, faz o score e o ranking, acrescenta metadados e indicadores customizados) -> cria df para o grafico1 -> retorna esse df em json para o plotly -> resultado volta para o index.html e cria o objeto chart, que é o grafico 1 -> executa a função que renderiza a tabela -> chama o endpoint /api/ranking -> executa a função price_repository (df com os preços e indicadores de todos os aticos) -> executa o run_pipeline (retorna o conteúdo em result["ranking"]) -> volta para o index.html e renderiza a tabela dentro do id "table" -> quando uma linha é selecionada, informa o ticker da ação -> candlechart.js ouve essa mensagem -> Chama o endpoint /api/candlechart passando o ticker selecionado -> consulta o price_repository para pegar os preços -> cria o plotly_data, que é consumido pelo gráfico 2

## Assistant

<thinking>
Let me analyze the project structure and files to understand the current implementation before making suggestions.
</thinking>

Deixa eu primeiro explorar a estrutura do projeto para entender como está organizado antes de fazer sugestões.

**Tool Call: List the `C:\Users\Bruno\trend` directory's contents**
Status: Completed

# Folders:
trend\.config
trend\.local
trend\.venv
trend\__pycache__
trend\app
trend\ui

# Files:
trend\.gitignore
trend\.replit
trend\15-03-2025_revisado.ipynb
trend\Dockerfile
trend\README 15-03-2025.TXT
trend\README.md
trend\main.py
trend\replit.md
trend\requirements.txt
trend\test_pipeline_chart_data.py


**Tool Call: List the `C:\Users\Bruno\trend\app` directory's contents**
Status: Completed

# Folders:
trend\app\__pycache__
trend\app\api
trend\app\charts
trend\app\core
trend\app\data
trend\app\finance
trend\app\services

# Files:
trend\app\config.py


**Tool Call: List the `C:\Users\Bruno\trend\ui` directory's contents**
Status: Completed

# Folders:
trend\ui\static
trend\ui\templates


**Tool Call: List the `C:\Users\Bruno\trend\app\api` directory's contents**
Status: Completed

# Folders:
trend\app\api\__pycache__

# Files:
trend\app\api\routes.py
trend\app\api\schemas.py


**Tool Call: List the `C:\Users\Bruno\trend\app\core` directory's contents**
Status: Completed

# Folders:
trend\app\core\__pycache__

# Files:
trend\app\core\config.py
trend\app\core\init.py
trend\app\core\pipeline.py
trend\app\core\price_repository.py


**Tool Call: List the `C:\Users\Bruno\trend\app\data` directory's contents**
Status: Completed

# Folders:
trend\app\data\__pycache__

# Files:
trend\app\data\market_data.py
trend\app\data\preprocessing.py
trend\app\data\schema.py


**Tool Call: List the `C:\Users\Bruno\trend\app\finance` directory's contents**
Status: Completed

# Folders:
trend\app\finance\__pycache__

# Files:
trend\app\finance\bollinger.py
trend\app\finance\indicators.py
trend\app\finance\macd.py
trend\app\finance\moving_averages.py
trend\app\finance\returns.py
trend\app\finance\trend.py
trend\app\finance\volatility.py


**Tool Call: List the `C:\Users\Bruno\trend\app\services` directory's contents**
Status: Completed

# Folders:
trend\app\services\__pycache__

# Files:
trend\app\services\ranking.py
trend\app\services\rules.py
trend\app\services\scoring.py


**Tool Call: List the `C:\Users\Bruno\trend\app\charts` directory's contents**
Status: Completed

C:\Users\Bruno\trend\app\charts is empty.


**Tool Call: Read file `app\core\pipeline.py`**
Status: Completed

```json
{
  "Text": "# \"\"\"\n# Pipeline para executar o primeiro grafico e filtrar os ativos.\n\n# Responsável por orquestrar:\n# - scoring\n# - ranking\n# - preparação de payload para API / frontend\n# \"\"\"\n\nfrom typing import Dict, Any\nimport pandas as pd\nimport numpy as np\n\nfrom app.data.market_data import (\n    list_b3_assets, get_asset_metadata, get_price_history, \n    download_price_history,\n    normalize_price_columns,\n    generate_theoretical_dates,\n    get_download_window, enrich_with_metadata_and_52w_high\n)\n\nfrom app.data.preprocessing import (\n    resolve_to_trading_dates,\n    extract_price_snapshots,\n    flatten_snapshot_for_scoring,\n    build_price_matrix_for_chart,\n    build_plotly_price_dataframe,\n    add_percent_change_for_hover,\n    extract_latest\n)\n\nfrom app.services.scoring import calculate_relative_strength\nfrom app.services.ranking import build_ranking\n\nfrom app.finance.moving_averages import simple_moving_average\nfrom app.finance.bollinger import calculate_bollinger_bands\nfrom app.finance.macd import calculate_macd\nfrom app.finance.volatility import calculate_atr_and_stop\n\nfrom app.finance.indicators import calculate_risk_return_indicators\n\n\nimport app.config as config\n\n\ndef run_pipeline(\n    prices: pd.DataFrame,\n    reference_date: str | None = None\n) -> Dict[str, Any]:\n    \"\"\"\n    Pipeline de ranking e visualização (etapas 5+).\n\n    Assume que o histórico de preços (`prices`) já foi:\n    - baixado\n    - normalizado\n    - enriquecido com indicadores técnicos (etapas 1–4)\n\n    Responsabilidades:\n    - resolver datas válidas\n    - extrair snapshots\n    - calcular força relativa\n    - ranquear ativos\n    - preparar payload para gráficos e tabela\n    \"\"\"\n\n    \n    df_latest = extract_latest(prices, price_field=\"Adj Close\", indicator_fields=None)\n    df_latest['Ticker'] = df_latest['Ticker'].astype(str).str.strip().str.upper()\n\n    # ------------------------------------------------------------------\n    # 5. Resolução das datas válidas e snapshots\n    # ------------------------------------------------------------------\n    theoretical_dates = generate_theoretical_dates(reference_date)\n    \n    trading_dates = resolve_to_trading_dates(\n        prices.index,\n        theoretical_dates\n    )    \n\n    price_snapshots = extract_price_snapshots(\n        prices,\n        trading_dates,\n        price_field=\"Adj Close\"\n    )\n        \n    df = flatten_snapshot_for_scoring(price_snapshots) #aqui o df deixa de ser multiindex    \n      \n\n    # ------------------------------------------------------------------\n    # 6. Scoring (Força Relativa)\n    # ------------------------------------------------------------------\n    scored = calculate_relative_strength(df)\n\n    if scored.empty:\n        return {\"summary\": {\"message\": \"Nenhum ativo pontuado\"},\n                \"ranking\": [], \"charts\": {}}\n                \n    \n    # ------------------------------------------------------------------\n    # 7. Ranking\n    # ------------------------------------------------------------------    \n    #aqui o df final é desprovido de qualquer coisa inicial; só tem as colunas com os preços nas datas selecionada, o ticker e o valor de FR e FR_Rank\n    ranking_result = build_ranking(\n    df=scored,\n    score_column=\"FR\",\n    min_score=config.MIN_FR,\n    top_n=config.TOP_N,\n    payload_fields=[\"FR\", \"FR_rank\"]\n    )\n    \n    if not ranking_result[\"payload\"]:\n        return {\n            \"summary\": {\"message\": \"Nenhum ativo passou no ranking\"},\n            \"ranking\": [],\n            \"charts\": {}\n        }\n    \n    # ------------------------------------------------------------------\n    # 9. Pós-ranking: merge + enriquecimento + indicadores finais\n    # ------------------------------------------------------------------\n    df_ranked = pd.DataFrame(ranking_result[\"payload\"])\n    df_ranked[\"ticker\"] = (\n        df_ranked[\"ticker\"]\n        .astype(str)\n        .str.strip()\n        .str.upper()\n    )\n\n    df_latest = df_latest.rename(columns={\"Ticker\": \"ticker\"})\n\n    df_ranked = df_ranked.merge(\n        df_latest,\n        on=\"ticker\",\n        how=\"left\",\n        validate=\"m:1\"\n    )\n\n    df_enriched = enrich_with_metadata_and_52w_high(\n        df=df_ranked,\n        ticker_column=\"ticker\"\n    )\n\n    df_final = calculate_risk_return_indicators(\n        df=df_enriched,\n        price_col=\"Adj Close\",\n        stop_col=\"STOP_ATR_14_1.5\",\n        high_52w_col=\"high_52w\"\n    )\n\n    # ------------------------------------------------------------------\n    # 10. Sanitização para JSON e montagem do payload\n    # ------------------------------------------------------------------\n    df_clean = df_final.copy()\n    df_clean.replace([np.inf, -np.inf], np.nan, inplace=True)\n\n    num = df_clean.select_dtypes(include=[np.number])\n    bad_mask = ~np.isfinite(num)\n\n    if bad_mask.any().any():\n        bad_cols = bad_mask.any()[bad_mask.any()].index.tolist()\n        print(\"Colunas com valores não finitos:\", bad_cols)\n\n    ranking_records = df_clean.to_dict(orient=\"records\")\n    print(df_clean)\n\n    for row in ranking_records:\n        for key, value in row.items():\n            if value is None:\n                continue\n            if isinstance(value, float) and not np.isfinite(value):\n                row[key] = None\n\n    summary = {\n        \"scored_assets\": len(scored),\n        \"ranked_assets\": len(ranking_records),\n        \"reference_date\": reference_date\n    }\n\n    charts = {\n        \"price_snapshots\": price_snapshots\n    }\n\n    return {\n        \"summary\": summary,\n        \"ranking\": ranking_records,\n        \"charts\": charts\n    }"
}
```

**Tool Call: Read file `app\core\init.py`**
Status: Completed

```json
{
  "Text": "# \"\"\"\n# Pipeline central da aplicação.\n\n# Responsável por orquestrar:\n# - download de dados\n# - cálculo de indicadores\n# - preparação o dataframe completo que será usado posteriormente\n# \"\"\"\n\nfrom typing import Dict, Any\nimport pandas as pd\nimport numpy as np\n\nfrom app.data.market_data import (\n    list_b3_assets, get_asset_metadata, get_price_history, \n    download_price_history,\n    normalize_price_columns,\n    generate_theoretical_dates,\n    get_download_window, enrich_with_metadata_and_52w_high\n)\n\nfrom app.data.preprocessing import (\n    resolve_to_trading_dates,\n    extract_price_snapshots,\n    flatten_snapshot_for_scoring,\n    build_price_matrix_for_chart,\n    build_plotly_price_dataframe,\n    add_percent_change_for_hover,\n    extract_latest\n)\n\nfrom app.services.scoring import calculate_relative_strength\nfrom app.services.ranking import build_ranking\n\nfrom app.finance.moving_averages import simple_moving_average\nfrom app.finance.bollinger import calculate_bollinger_bands\nfrom app.finance.macd import calculate_macd\nfrom app.finance.volatility import calculate_atr_and_stop\n\nfrom app.finance.indicators import calculate_risk_return_indicators\n\n\nimport app.config as config\n\n\ndef init(reference_date: str | None = None) -> pd.DataFrame:\n    \"\"\"\n    Pipeline base (etapas 1–4).\n\n    Responsável por:\n    - definir universo de ativos\n    - baixar histórico de preços\n    - normalizar dados\n    - calcular indicadores técnicos\n    \"\"\"\n    print(\"iniciando função\")\n\n    # ------------------------------------------------------------------\n    # 1. Universo de ativos\n    # ------------------------------------------------------------------\n    tickers = list_b3_assets(\n        min_price=config.MIN_PRICE,\n        min_volume=config.MIN_VOLUME,\n        excluded_suffixes=config.EXCLUDE_SUFFIXES\n    )\n    #print(tickers)\n\n    if not tickers:\n        raise RuntimeError(\"Nenhum ativo encontrado para os filtros definidos\")\n    # else:\n        # print(\"tickers obtidos\")\n\n    # ------------------------------------------------------------------\n    # 2. Datas teóricas e janela mínima\n    # ------------------------------------------------------------------\n    theoretical_dates = generate_theoretical_dates(\n        reference_date or pd.Timestamp.today(),\n        periods=config.ANALYSIS_MONTHS + 1\n    )\n\n    start_date, end_date = get_download_window(theoretical_dates)\n\n    # ------------------------------------------------------------------\n    # 3. Download único do histórico\n    # ------------------------------------------------------------------\n    prices = download_price_history(\n        tickers=tickers,\n        start=start_date,\n        end=end_date,\n        progress=True\n    )\n\n    if prices.empty:\n        raise RuntimeError(\"Histórico de preços vazio\")\n\n    prices = normalize_price_columns(prices) #normalizar é tratar o multiindex\n\n    # ------------------------------------------------------------------\n    # 4. Indicadores técnicos (histórico completo)\n    # ------------------------------------------------------------------\n    prices = simple_moving_average(\n        prices,\n        price_field=\"Adj Close\",\n        window=config.MA_WINDOW\n    )\n\n    prices = calculate_bollinger_bands(\n        prices,\n        window=config.BOLLINGER_WINDOW,\n        num_std=config.BOLLINGER_STD\n    )\n\n    prices = calculate_macd(\n        prices,\n        fast_window=config.MACD_FAST,\n        slow_window=config.MACD_SLOW,\n        signal_window=config.MACD_SIGNAL\n    )\n\n    prices = calculate_atr_and_stop(\n        prices,\n        window=config.ATR_WINDOW,\n        multiplier=config.ATR_MULTIPLIER\n    )    \n    #debug\n    prices.to_clipboard()\n    \n    # ------------------------------------------------------------------\n    # 10. Sanitização para JSON e montagem do payload\n    # ------------------------------------------------------------------\n    df_clean = prices.copy()\n    df_clean.replace([np.nan, np.inf, -np.inf], 0, inplace=True) #aqui está substituindo por zero\n    #df_clean = df_clean.fillna(np.nan).replace([np.nan, np.inf, -np.inf], [None, None, None]) #aqui substitui por None, mas dá errado ainda\n\n                    \n    return df_clean"
}
```

**Tool Call: Read file `app\core\price_repository.py`**
Status: Completed

```json
{
  "Text": "from typing import Dict\nimport pandas as pd\n\n\nclass PriceRepository:\n    \"\"\"\n    Repositório em memória para armazenar históricos de preços (`prices`)\n    indexados pela data de referência.\n\n    Responsabilidades:\n    - armazenar DataFrames em memória\n    - recuperar DataFrames por reference_date\n    - informar se um histórico já existe\n\n    Escopo:\n    - memória do processo (1 worker)\n    - dados voláteis (descartados ao reiniciar a aplicação)\n    \"\"\"\n\n    def __init__(self) -> None:\n        self._store: Dict[str, pd.DataFrame] = {}\n        self._current_reference_date: str | None = None\n\n    def has(self, reference_date: str) -> bool:\n        \"\"\"\n        Verifica se existe histórico de preços para a data de referência.\n        \"\"\"\n        return reference_date in self._store\n\n    def get(self, reference_date: str) -> pd.DataFrame:\n        \"\"\"\n        Recupera o histórico de preços associado à data de referência.\n\n        Levanta KeyError se não existir.\n        \"\"\"\n        if reference_date not in self._store:\n            raise KeyError(\n                f\"Prices não encontrado para reference_date={reference_date}\"\n            )\n        return self._store[reference_date]\n\n    def set(self, reference_date: str, prices: pd.DataFrame) -> None:\n        \"\"\"\n        Armazena (ou sobrescreve) o histórico de preços para a data de referência.\n        \"\"\"\n        if not isinstance(prices, pd.DataFrame):\n            raise TypeError(\"prices deve ser um pandas.DataFrame\")\n\n        self._store[reference_date] = prices\n        self._current_reference_date = reference_date\n    \n    def current_reference_date(self) -> str:\n        \"\"\"\n        Retorna a data de referência atualmente ativa.\n\n        Levanta RuntimeError se nenhuma data tiver sido inicializada.\n        \"\"\"\n        if self._current_reference_date is None:\n            raise RuntimeError(\"Nenhuma reference_date foi inicializada ainda\")\n        return self._current_reference_date\n\n    def clear(self) -> None:\n        \"\"\"\n        Remove todos os históricos armazenados (útil para debug ou testes).\n        \"\"\"\n        self._store.clear()\n        self._current_reference_date = None\n\n\n# Instância única do repositório (escopo de aplicação)\nprice_repository = PriceRepository()"
}
```

**Tool Call: Read file `app\api\routes.py`**
Status: Completed

```json
{
  "Text": "from fastapi import APIRouter, Query, HTTPException\nfrom typing import Optional\n\nimport pandas as pd\nimport numpy as np\nfrom datetime import date\n\nfrom app.core.pipeline import run_pipeline\nfrom app.core.init import init\nfrom app.core.price_repository import price_repository\nfrom app.data.preprocessing import build_price_matrix_for_chart, build_plotly_payload\n\nimport app.config as config\n\nrouter = APIRouter()\n\n\n@router.get(\"/fr-price-series\")\ndef get_fr_price_series(\n    reference_date: Optional[str] = Query(\n        default=str(date.today()),\n        description=\"Data de referência no formato YYYY-MM-DD\"\n    )\n):\n    \"\"\"\n    Endpoint para geração do gráfico de validação da Força Relativa (FR).\n\n    Retorna um payload JSON pronto para consumo pelo Plotly JS.\n    \"\"\"\n\n    # ------------------------------------------------------------------\n    # 1. Garante inicialização do histórico de preços (etapas 1–4)\n    # ------------------------------------------------------------------\n    # se ainda não existir histórico para a data, inicializa (etapas 1–4)\n    if not price_repository.has(reference_date):\n        prices = init(reference_date)\n        price_repository.set(reference_date, prices)\n    \n    # recupera o histórico de preços já inicializado\n    prices = price_repository.get(reference_date)\n\n    # ------------------------------------------------------------------\n    # 2. Executa pipeline de ranking / snapshots (etapas 5+)\n    # ------------------------------------------------------------------\n    \n    # executa pipeline de ranking / snapshots (etapas 5+)\n    result = run_pipeline(prices=prices, reference_date=reference_date)\n\n    if \"charts\" not in result or \"price_snapshots\" not in result[\"charts\"]:\n        raise HTTPException(\n            status_code=500,\n            detail=\"price_snapshots não disponível no pipeline\"\n        )\n\n    price_snapshots = result[\"charts\"][\"price_snapshots\"]\n\n    ranking = result.get(\"ranking\", [])\n    if not ranking:\n        raise HTTPException(\n            status_code=404,\n            detail=\"Nenhum ativo ranqueado\"\n        )\n    # ------------------------------------------------------------------\n    # 2. Extrai tickers selecionados\n    # ------------------------------------------------------------------\n    selected_tickers = [\n        item[\"ticker\"]\n        for item in ranking\n        if item.get(\"FR_rank\", 0) >= config.MIN_FR\n    ]\n\n    if not selected_tickers:\n        raise HTTPException(\n            status_code=404,\n            detail=\"Nenhum ativo atende ao critério mínimo de FR\"\n        )\n\n    # ------------------------------------------------------------------\n    # 3. Monta matriz de preços para o gráfico\n    # ------------------------------------------------------------------\n    df_chart = build_price_matrix_for_chart(\n        price_snapshots=price_snapshots,\n        selected_tickers=selected_tickers,\n        price_field=\"Adj Close\"\n    )\n\n    # ------------------------------------------------------------------\n    # 4. Monta payload Plotly\n    # ------------------------------------------------------------------\n    plotly_data = build_plotly_payload(df_chart)\n\n    layout = {\n        \"title\": \"Validação da Força Relativa (FR)\",\n        \"xaxis\": {\n            \"title\": \"Data\",\n            \"type\": \"date\"\n        },\n        \"yaxis\": {\n            \"title\": \"Preço Ajustado (Adj Close)\",\n            \"tickformat\": \".2f\"\n        },\n        \"hovermode\": \"closest\",\n        \"legend\": {\n            \"orientation\": \"h\",\n            \"y\": -0.3\n        }\n    }\n\n    return {\n        \"data\": plotly_data,\n        \"layout\": layout        \n    }\n    \n@router.get(\"/ranking\")\ndef api_ranking():\n    \"\"\"\n    Retorna o ranking/resultados do pipeline como JSON (lista de objetos).\n    O run_pipeline deve aceitar reference_date (ou adapte a chamada).\n    \"\"\"\n    # recupera a data de referência atualmente ativa\n    reference_date = price_repository.current_reference_date()\n\n    # garante que o histórico de preços exista\n    if not price_repository.has(reference_date):\n        prices = init(reference_date)\n        price_repository.set(reference_date, prices)\n\n    prices = price_repository.get(reference_date)\n\n    result = run_pipeline(prices=prices, reference_date=reference_date)\n\n    return result[\"ranking\"]\n\n@router.get(\"/candlechart\")    \ndef get_candlechart(ticker: str = Query(..., description=\"Ticker do ativo selecionado\")):\n    \"\"\"\n    gera gráfico de candles a partir do ticker da linha selecionada na tabela.    \n    usa o dataframe completo 'prices' com dados dos ativos selecionados.\n    calcula os indicadores medias moveis, bandas de bollinger, STOP_ATR, risco e retorno_risco    \n    Retorna um payload JSON pronto para consumo pelo Plotly JS.\n    \"\"\"        \n    #pega o prices e extrai somente os ativos selecionados\n    #faz um slice só do ativo selecionado\n    #calcula os indicadores e adiciona no dataframe\n    #monta o dataframe final (e salva em cache? poderia, porque o mesmo ticker pode ser selecionado de novo pelo usuário)\n    #Monta payload Plotly\n    \n    reference_date = price_repository.current_reference_date()\n    prices = price_repository.get(reference_date)\n    ticker = ticker.strip().upper()    \n    \n    # slice do ativo selecionado preservando o eixo temporal\n    df_ticker = prices.xs(ticker, level=\"Ticker\", axis=1).copy()\n    df_ticker[\"volume_medio\"] = df_ticker['Volume'].rolling(window=20).mean()\n    \n    # print(\"estrutura final do df\")\n    # print(df_ticker.columns)\n    \n    if df_ticker.empty:\n        raise HTTPException(\n            status_code=404,\n            detail=f\"Ticker {ticker} não encontrado no histórico carregado\"\n        )\n    \n    #falta selecionar as colunas e montar a estrutura esperada pelo plotly_data\n    # ------------------------------------------------------------------\n    # Seleção das colunas OHLC e preparação para Plotly\n    # ------------------------------------------------------------------\n    # garante ordenação temporal\n    df_clean = df_ticker.sort_index()\n    \n    start_idx = 20\n    # slice para ignorar período sem indicadores\n    df_plot = df_clean.iloc[start_idx:]\n        \n    # Agora cada coluna pode ser convertida em lista sem erro ao gerar JSON\n    datas = df_plot.index.to_pydatetime().tolist() # extrai eixo temporal\n    open_prices = df_plot[\"Open\"].astype(float).tolist()\n    high_prices = df_plot[\"High\"].astype(float).tolist()\n    low_prices = df_plot[\"Low\"].astype(float).tolist()\n    close_prices = df_plot[\"Close\"].astype(float).tolist()\n    sma_20 = df_plot[\"SMA_20\"].tolist() \n    bb_upper_20 = df_plot[\"BB_UPPER_20\"].tolist()\n    bb_lower_20 = df_plot[\"BB_LOWER_20\"].tolist()\n    macd = df_plot[\"MACD_12_26\"].tolist()\n    macd_signal = df_plot[\"MACD_SIGNAL_9\"].tolist()\n    macd_hist = df_plot[\"MACD_HIST_12_26_9\"].tolist()\n    stop_atr = df_plot[\"STOP_ATR_14_1.5\"].tolist()\n    volume = df_plot[\"Volume\"].tolist()\n    volume_medio = df_plot[\"volume_medio\"].tolist()    \n    \n    \n    \n    plotly_data = []  # começa vazio e vai adicionando as traces\n\n    # Candlestick no eixo principal (yaxis)\n    print(\"adicionando candlestick\")\n    plotly_data.append({\n        \"type\": \"candlestick\",\n        \"x\": datas,\n        \"open\": open_prices,\n        \"high\": high_prices,\n        \"low\": low_prices,\n        \"close\": close_prices,\n        \"name\": ticker,\n        \"yaxis\": \"y\"\n    })\n\n    # SMA\n    print(\"adicionando sma\")\n    plotly_data.append({\n        \"type\": \"scatter\",\n        \"mode\": \"lines\",\n        \"x\": datas,\n        \"y\": df_plot[\"SMA_20\"].astype(float).tolist(),\n        \"name\": \"SMA\",\n        \"line\": {\"color\": \"black\"},\n        \"yaxis\": \"y\"\n    })\n\n    # Upper Band\n    print(\"adicionando bbands up\")\n    plotly_data.append({\n        \"type\": \"scatter\",\n        \"mode\": \"lines\",\n        \"x\": datas,\n        \"y\": df_plot[\"BB_UPPER_20\"].astype(float).tolist(),\n        \"name\": \"Upper Band\",\n        \"line\": {\"dash\": \"dash\", \"color\": \"gray\"},\n        \"opacity\": 0.5,\n        \"yaxis\": \"y\"\n    })\n\n    # Lower Band com preenchimento\n    print(\"adicionando bbands low\")\n    plotly_data.append({\n        \"type\": \"scatter\",\n        \"mode\": \"lines\",\n        \"x\": datas,\n        \"y\": df_plot[\"BB_LOWER_20\"].astype(float).tolist(),\n        \"name\": \"Lower Band\",\n        \"line\": {\"dash\": \"dash\", \"color\": \"gray\"},\n        \"fill\": \"tonexty\",\n        \"opacity\": 0.5,\n        \"yaxis\": \"y\"\n    })\n\n    # Volume no subplot (yaxis2)\n    print(\"adicionando volume\")\n    plotly_data.append({\n        \"type\": \"bar\",\n        \"x\": datas,\n        \"y\": df_plot[\"Volume\"].tolist(),\n        \"marker\": {\n            \"color\": [\"green\" if c > o else \"red\" for o, c in zip(open_prices, close_prices)]\n        },\n        \"name\": \"Volume\",\n        \"yaxis\": \"y2\",\n        \"showlegend\": False\n    })\n    \n    # Volume Médio\n    plotly_data.append({\n        \"type\": \"scatter\",\n        \"mode\": \"lines\",\n        \"x\": datas,\n        \"y\": volume_medio,\n        \"name\": \"Volume Médio\",\n        \"line\": {\"color\": \"blue\"},\n        \"yaxis\": \"y2\"\n    })\n\n    # STOP ATR\n    plotly_data.append({\n        \"type\": \"scatter\",\n        \"mode\": \"lines\",\n        \"x\": datas,\n        \"y\": df_plot[\"STOP_ATR_14_1.5\"].tolist(),\n        \"name\": \"STOP ATR\",\n        \"line\": {\"shape\": \"hv\", \"color\": \"red\"},\n        \"yaxis\": \"y\"\n    })\n    \n    # MACD\n    print(\"adicionando MACD\")\n    plotly_data.append({\n        \"type\": \"scatter\",\n        \"mode\": \"lines\",\n        \"x\": datas,\n        \"y\": df_plot[\"MACD_12_26\"].tolist(),\n        \"name\": \"MACD\",\n        \"line\": {\"color\": \"black\"},\n        \"yaxis\": \"y3\"\n    })\n\n    plotly_data.append({\n        \"type\": \"scatter\",\n        \"mode\": \"lines\",\n        \"x\": datas,\n        \"y\": df_plot[\"MACD_SIGNAL_9\"].tolist(),\n        \"name\": \"MACD Signal\",\n        \"line\": {\"dash\": \"dash\", \"color\": \"gray\"},\n        \"opacity\": 0.5,\n        \"yaxis\": \"y3\"\n    })\n\n    plotly_data.append({\n        \"type\": \"bar\",\n        \"x\": datas,\n        \"y\": df_plot[\"MACD_HIST_12_26_9\"].tolist(),\n        \"name\": \"MACD Hist\",\n        \"marker\": {\"color\": \"gray\"},\n        \"yaxis\": \"y3\"\n    })\n\n\n    # Layout com domínio vertical separado\n    layout = {\n        \"height\": 650,\n        \"title\": f\"Candlestick – {ticker}\",\n        \"xaxis\": {\n            \"title\": \"Data\",\n            \"type\": \"date\",\n            \"rangeslider\": {\"visible\": False},\n            \"rangebreaks\": [{\"bounds\": [\"sat\", \"mon\"]}]\n        },\n        \"yaxis\": {  # Candlestick + indicadores principais\n            \"title\": \"Preço\",\n            \"domain\": [0.3, 1],  # ocupa 70% da altura,\n            \"autorange\": True,\n            \"rangemode\": \"normal\"\n        },\n        \"yaxis2\": {  # Volume\n            \"title\": \"Volume\",\n            \"domain\": [0.15, 0.3],  # ocupa 30% inferior\n            \"showgrid\": False\n        },\n        \"yaxis3\": {  # MACD\n            \"title\": \"MACD\",\n            \"domain\": [0, 0.15],  # ocupa 30% inferior\n            \"showgrid\": False\n        },\n        \"hovermode\": \"x unified\"\n    }\n\n    return {\n        \"data\": plotly_data,\n        \"layout\": layout\n    }\n    \n        \n    \n    \n        \n     "
}
```

**Tool Call: Read file `app\services\ranking.py`**
Status: Completed

```json
{
  "Text": "\"\"\"\nResponsável por ordenar, filtrar e estruturar os ativos pontuados.\n\nEsta camada NÃO calcula indicadores.\nEla apenas transforma scores (ex: Força Relativa) em ranking consumível\npor pipeline, API e frontend.\n\"\"\"\n\nfrom typing import List, Dict, Any\nimport pandas as pd\n\n\ndef rank_assets(df: pd.DataFrame,\n                score_column: str = \"FR\",\n                min_score: float = 0.0,\n                top_n: int | None = None) -> pd.DataFrame:\n    \"\"\"\n    Ordena os ativos com base em uma coluna de score.\n\n    Parâmetros\n    ----------\n    df : pd.DataFrame\n        DataFrame contendo os ativos já pontuados.\n    score_column : str\n        Nome da coluna que contém o score (default: 'FR').\n    min_score : float\n        Score mínimo para o ativo ser considerado.\n    top_n : int | None\n        Quantidade máxima de ativos retornados.\n\n    Retorno\n    -------\n    pd.DataFrame\n        DataFrame ordenado do maior para o menor score.\n    \"\"\"\n\n    if score_column not in df.columns:\n        raise ValueError(\n            f\"Coluna '{score_column}' não encontrada no DataFrame\")\n\n    ranked = (df[df[score_column] >= min_score].sort_values(\n        by=score_column, ascending=False).reset_index(drop=True))\n\n    if top_n is not None:\n        ranked = ranked.head(top_n)\n\n    return ranked\n\n\ndef ranking_to_payload(df: pd.DataFrame,\n                       fields: List[str] | None = None) -> List[Dict]:\n    \"\"\"\n    Converte o ranking em estrutura serializável (JSON-like).\n\n    Parâmetros\n    ----------\n    df : pd.DataFrame\n        DataFrame já ordenado.\n    fields : list[str] | None\n        Lista de campos a incluir no payload.\n        Se None, inclui todas as colunas.\n\n    Retorno\n    -------\n    list[dict]\n        Ranking pronto para retorno em API.\n    \"\"\"\n\n    if fields is not None:\n        missing = set(fields) - set(df.columns)\n        if missing:\n            raise ValueError(f\"Campos ausentes no DataFrame: {missing}\")\n        df = df[fields]\n\n    return df.to_dict(orient=\"records\")\n\n\ndef build_ranking(\n    df: pd.DataFrame,\n    score_column: str = \"FR\",\n    min_score: float | None = None,\n    top_n: int | None = None,\n    payload_fields: List[str] | None = None\n) -> Dict[str, Any]:\n    \"\"\"\n    Constrói o ranking de ativos a partir de um score contínuo (ex.: FR),\n    gerando adicionalmente um score ordinal percentual (FR_rank).\n\n    CONTRATO\n    --------\n    - df deve ser um DataFrame flat\n    - índice representa o ticker\n    - score_column deve existir no DataFrame\n    - a função NÃO calcula indicadores nem scores primários\n\n    LÓGICA\n    ------\n    1. Ordena os ativos pelo score contínuo (descendente)\n    2. Constrói FR_rank (0–100) com base na posição relativa\n    3. Aplica filtros usando FR_rank\n    4. Prepara payload final\n    \"\"\"\n\n    # ------------------------------------------------------------------\n    # Validações iniciais\n    # ------------------------------------------------------------------\n    #print(\"df recebido no build_ranking\")\n    #print(df)\n    #print(df.columns)\n    \n    if df is None or df.empty:\n        raise ValueError(\"DataFrame vazio recebido em build_ranking\")\n\n    if not df.index.is_unique:\n        raise ValueError(\"Índice do DataFrame deve ser único (ticker)\")\n\n    if score_column not in df.columns:\n        raise ValueError(f\"Coluna de score '{score_column}' não encontrada\")\n\n    # ------------------------------------------------------------------\n    # Trabalho sobre cópia explícita\n    # ------------------------------------------------------------------\n    ranked = df.copy()\n\n    ranked = ranked[ranked[score_column].notna()]\n\n    if ranked.empty:\n        return {\"ranking\": ranked, \"payload\": []}\n\n    # ------------------------------------------------------------------\n    # Ordenação pelo score contínuo\n    # ------------------------------------------------------------------\n    ranked = ranked.sort_values(by=score_column, ascending=False)\n\n    # ------------------------------------------------------------------\n    # Criação do FR_rank (percentil 0–100)\n    # ------------------------------------------------------------------\n    ranked[\"FR_rank\"] = (\n        ranked[score_column]\n        .rank(method=\"first\", ascending=False, pct=True)\n        * 100\n    ).round(2)\n\n    # ------------------------------------------------------------------\n    # Filtro por FR_rank\n    # ------------------------------------------------------------------\n    if min_score is not None:\n        ranked = ranked[ranked[\"FR_rank\"] >= min_score]\n        #print(\"df final\")\n        #print(ranked)\n        #print(ranked.columns)\n        #print(ranked.index)\n\n    if ranked.empty:\n        return {\"ranking\": ranked, \"payload\": []}\n\n    # ------------------------------------------------------------------\n    # Limite de quantidade\n    # ------------------------------------------------------------------\n    if top_n is not None:\n        ranked = ranked.head(top_n)\n\n    # ------------------------------------------------------------------\n    # Construção do payload\n    # ------------------------------------------------------------------\n    payload = []\n    fields = payload_fields or []\n\n    for ticker, row in ranked.iterrows():\n        item = {\"ticker\": ticker}\n\n        for field in fields:\n            if field not in ranked.columns:\n                raise ValueError(\n                    f\"Campo '{field}' solicitado no payload não existe no DataFrame\"\n                )\n            item[field] = row[field]\n\n        # Scores sempre disponíveis\n        item[\"FR\"] = row[score_column]\n        item[\"FR_rank\"] = row[\"FR_rank\"]\n\n        payload.append(item)\n\n    return {\n        \"ranking\": ranked,\n        \"payload\": payload\n    }"
}
```

**Tool Call: Read file `app\services\scoring.py`**
Status: Completed

```json
{
  "Text": "\"\"\"\nscoring.py\n\nCamada responsável pelo cálculo de métricas de pontuação (scores)\ndos ativos, com foco na Força Relativa (FR).\n\nEste módulo contém apenas lógica matemática e estatística.\nNão realiza ordenação, filtros finais, IO, visualização ou decisões\nde alocação.\n\"\"\"\n\nfrom __future__ import annotations\n\nimport pandas as pd\nimport numpy as np\n\n#regra de ouro: aqui nenhuma função deve receber dataframe multiindex\n\ndef calculate_relative_strength(df: pd.DataFrame) -> pd.DataFrame:\n    \"\"\"\n    Calcula o score de Força Relativa (FR) de cada ativo, preservando\n    integralmente a estrutura tabular recebida.\n\n    CONTRATO DA FUNÇÃO\n    ------------------\n    - Esta função NÃO recebe DataFrames com MultiIndex.\n    - O DataFrame deve estar em formato flat, com:\n        index  -> ticker\n        columns -> p0, p1, ..., pN (preços históricos ordenados\n                   do mais antigo para o mais recente)\n                   + quaisquer outras colunas auxiliares.\n    - A função apenas adiciona a coluna 'FR'.\n\n    LÓGICA DO CÁLCULO\n    -----------------\n    A Força Relativa é calculada a partir das variações percentuais\n    entre cada preço histórico e o preço mais recente (pN),\n    ponderadas pela raiz quadrada da distância temporal.\n\n    Para N preços:\n        var_i = (p_i / p_N) - 1\n        peso_i = sqrt(N - i)\n\n    FR = soma(var_i * peso_i) / soma(peso_i)\n\n    Essa lógica é equivalente à função original baseada em\n    colunas posicionais, porém agora generalizada e vetorizada.\n\n    ERROS\n    -----\n    - Lança ValueError se:\n        - DataFrame estiver vazio\n        - índice não for único\n        - menos de 2 colunas de preço (p*)\n    \"\"\"\n\n    # ------------------------------------------------------------------\n    # Validações estruturais\n    # ------------------------------------------------------------------\n    if df is None or df.empty:\n        raise ValueError(\"DataFrame vazio recebido em calculate_relative_strength\")\n\n    if not df.index.is_unique:\n        raise ValueError(\"Índice do DataFrame deve ser único (ticker)\")\n\n    # Identifica colunas de preço (prefixo 'p')\n    price_cols = [c for c in df.columns if c.startswith(\"p\")]\n\n    if len(price_cols) < 2:\n        raise ValueError(\n            \"São necessárias ao menos duas colunas de preço (p0, p1, ...)\"\n        )\n\n    # Garante ordenação correta das colunas de preço\n    price_cols = sorted(\n        price_cols,\n        key=lambda x: int(x.replace(\"p\", \"\"))\n    )\n\n    # ------------------------------------------------------------------\n    # Extração da matriz de preços\n    # ------------------------------------------------------------------\n    prices = df[price_cols]\n\n    # Preço mais recente (última coluna)\n    p_last = prices.iloc[:, -1]\n\n    # ------------------------------------------------------------------\n    # Cálculo vetorial das variações\n    # ------------------------------------------------------------------\n    variations = prices.div(p_last, axis=0) - 1.0\n\n    # Remove a última coluna (variação zero contra ela mesma)\n    variations = variations.iloc[:, :-1]\n\n    # ------------------------------------------------------------------\n    # Pesos temporais (raiz quadrada)\n    # ------------------------------------------------------------------\n    n_periods = variations.shape[1]\n\n    weights = np.sqrt(\n        np.arange(n_periods, 0, -1)\n    )\n\n    # Normalização dos pesos\n    weights = weights / weights.sum()\n\n    # ------------------------------------------------------------------\n    # Cálculo do FR\n    # ------------------------------------------------------------------\n    fr_values = variations.mul(weights, axis=1).sum(axis=1)\n\n    # ------------------------------------------------------------------\n    # Inserção do resultado preservando o DataFrame original\n    # ------------------------------------------------------------------\n    df_out = df.copy()\n    df_out[\"FR\"] = fr_values.round(6)\n\n    return df_out"
}
```

**Tool Call: Read file `app\data\preprocessing.py`**
Status: Completed

```json
{
  "Text": "from typing import Dict, Any, Optional, List\nimport pandas as pd\n\ndef resolve_to_trading_dates(\n    index: pd.DatetimeIndex,\n    theoretical_dates: list[pd.Timestamp]\n) -> list[pd.Timestamp]:\n    \"\"\"\n    Para cada data teórica, encontra o último pregão disponível\n    anterior ou igual à data.\n    \"\"\"\n    resolved = []\n\n    for d in theoretical_dates:\n        valid_dates = index[index <= d]\n        if valid_dates.empty:\n            raise ValueError(\n                f\"Não há dados de mercado antes de {d.date()}\"\n            )\n        resolved.append(valid_dates.max())\n\n    return resolved\n\ndef extract_price_snapshots(\n    prices: pd.DataFrame,\n    trading_dates: list[pd.Timestamp],\n    price_field: str = \"Adj Close\"\n) -> pd.DataFrame:\n    \"\"\"\n    Extrai snapshots de preço para datas específicas,\n    assumindo colunas MultiIndex (Field, Ticker).\n    \"\"\"\n    return prices.loc[\n        trading_dates,\n        prices.columns.get_level_values(\"Field\") == price_field\n    ]\n\ndef flatten_snapshot_for_scoring(\n    snapshot: pd.DataFrame,\n    price_field: str = \"Adj Close\",\n    prefix: str = \"p\"\n) -> pd.DataFrame:\n    \"\"\"\n    Converte um snapshot histórico MultiIndex em um DataFrame tabular\n    (flat) adequado para cálculo de Força Relativa (FR).\n\n    A função reorganiza os dados de forma que:\n    - cada linha represente um ativo (ticker)\n    - cada coluna represente um preço em uma data distinta\n    - as datas sejam ordenadas do período mais antigo para o mais recente\n\n    CONTRATO DA FUNÇÃO\n    ------------------\n    - Esta função RECEBE um DataFrame com:\n        index : DatetimeIndex (múltiplas datas)\n        columns : MultiIndex com níveis ['Field', 'Ticker']\n    - Esta função DEVOLVE um DataFrame com:\n        index : ticker\n        columns : colunas simples (Index plano), contendo preços históricos\n\n    A função NÃO:\n    - calcula Força Relativa\n    - normaliza dados\n    - remove ativos com NaN\n    - adiciona indicadores técnicos\n    - faz merges ou joins\n\n    PARÂMETROS\n    ----------\n    snapshot : pandas.DataFrame\n        DataFrame MultiIndex contendo múltiplas datas e ativos.\n\n    price_field : str, default=\"Adj Close\"\n        Nome do campo de preço a ser utilizado no cálculo de FR.\n\n    prefix : str, default=\"p\"\n        Prefixo usado para nomear as colunas de preço (ex.: p0, p1, p2...).\n\n    RETORNO\n    -------\n    pandas.DataFrame\n        DataFrame flat com:\n            - índice: ticker\n            - colunas: preços históricos ordenados temporalmente\n\n        Exemplo de colunas:\n            p0, p1, p2, ..., pN\n\n    ERROS\n    -----\n    ValueError se:\n        - snapshot estiver vazio\n        - snapshot não tiver MultiIndex nas colunas\n        - price_field não existir no nível 'Field'\n        - snapshot contiver menos de duas datas\n    \"\"\"\n\n    # ------------------------------------------------------------------\n    # Validações estruturais\n    # ------------------------------------------------------------------\n    if snapshot is None or snapshot.empty:\n        raise ValueError(\"Snapshot vazio recebido em flatten_snapshot_for_scoring\")\n\n    if not isinstance(snapshot.columns, pd.MultiIndex):\n        raise ValueError(\"Snapshot deve possuir colunas MultiIndex\")\n\n    if \"Field\" not in snapshot.columns.names or \"Ticker\" not in snapshot.columns.names:\n        raise ValueError(\"Snapshot deve ter níveis de coluna ['Field', 'Ticker']\")\n\n    if price_field not in snapshot.columns.get_level_values(\"Field\"):\n        raise ValueError(f\"Campo de preço '{price_field}' não encontrado no snapshot\")\n\n    if snapshot.shape[0] < 2:\n        raise ValueError(\"Snapshot deve conter ao menos duas datas para cálculo de FR\")\n\n    # ------------------------------------------------------------------\n    # Seleção do campo de preço\n    # ------------------------------------------------------------------\n    prices = snapshot.loc[:, price_field]\n\n    # prices:\n    # index  -> Date\n    # columns -> Ticker\n\n    # ------------------------------------------------------------------\n    # Ordenação temporal explícita\n    # ------------------------------------------------------------------\n    prices = prices.sort_index()\n\n    # ------------------------------------------------------------------\n    # Reorganização: datas viram colunas\n    # ------------------------------------------------------------------\n    prices_t = prices.T\n\n    # prices_t:\n    # index   -> Ticker\n    # columns -> Date\n\n    # ------------------------------------------------------------------\n    # Renomeação das colunas (datas -> p0, p1, ..., pN)\n    # ------------------------------------------------------------------\n    new_columns = {\n        date: f\"{prefix}{i}\"\n        for i, date in enumerate(prices_t.columns)\n    }\n\n    prices_t = prices_t.rename(columns=new_columns)\n\n    # ------------------------------------------------------------------\n    # Garantias finais\n    # ------------------------------------------------------------------\n    prices_t.index.name = \"ticker\"\n\n    return prices_t\n\ndef build_price_matrix_for_chart(\n    price_snapshots: pd.DataFrame,\n    selected_tickers: list[str],\n    price_field: str = \"Adj Close\",\n) -> pd.DataFrame:\n    \"\"\"\n    Constrói o DataFrame de entrada para o gráfico de validação do FR.\n\n    A função recebe um snapshot de preços em formato MultiIndex\n    (Field, Ticker) x Date e retorna uma matriz tabular simples,\n    com uma linha por ativo e uma coluna por data.\n\n    Parâmetros\n    ----------\n    price_snapshots : pandas.DataFrame\n        DataFrame MultiIndex com:\n        - index: datas (datetime)\n        - columns: MultiIndex ['Field', 'Ticker']\n\n    selected_tickers : list[str]\n        Lista de tickers selecionados (ex.: FR_rank >= min_score).\n\n    price_field : str, default=\"Adj Close\"\n        Campo de preço a ser utilizado.\n\n    Retorno\n    -------\n    pandas.DataFrame\n        DataFrame com:\n        - index: ticker\n        - columns: datas (ordenadas, datetime)\n        - valores: preços ajustados\n    \"\"\"\n\n    if price_snapshots.empty:\n        raise ValueError(\"price_snapshots está vazio\")\n\n    if not selected_tickers:\n        raise ValueError(\"Lista de tickers selecionados está vazia\")\n\n    if not isinstance(price_snapshots.columns, pd.MultiIndex):\n        raise ValueError(\"price_snapshots deve possuir colunas MultiIndex\")\n\n    if \"Field\" not in price_snapshots.columns.names:\n        raise ValueError(\"Nível 'Field' não encontrado nas colunas\")\n\n    if \"Ticker\" not in price_snapshots.columns.names:\n        raise ValueError(\"Nível 'Ticker' não encontrado nas colunas\")\n\n    # ------------------------------------------------------------------\n    # 1. Seleciona apenas o campo de preço desejado\n    # ------------------------------------------------------------------\n    try:\n        prices_field = price_snapshots.loc[:, price_field]\n    except KeyError as exc:\n        raise ValueError(\n            f\"Campo de preço '{price_field}' não encontrado no snapshot\"\n        ) from exc\n\n    # prices_field:\n    # index  -> Date\n    # columns -> Ticker\n\n    # ------------------------------------------------------------------\n    # 2. Filtra apenas os tickers selecionados\n    # ------------------------------------------------------------------\n    missing = set(selected_tickers) - set(prices_field.columns)\n    if missing:\n        raise ValueError(\n            f\"Tickers ausentes no snapshot de preços: {missing}\"\n        )\n\n    prices_filtered = prices_field[selected_tickers]\n\n    # ------------------------------------------------------------------\n    # 3. Reorganiza para formato final (ticker x datas)\n    # ------------------------------------------------------------------\n    df_chart = prices_filtered.T\n\n    # Garante ordenação temporal das colunas\n    df_chart = df_chart.sort_index(axis=1)\n\n    # ------------------------------------------------------------------\n    # 4. Valida estrutura final\n    # ------------------------------------------------------------------\n    if not df_chart.index.is_unique:\n        raise ValueError(\"Índice final (ticker) não é único\")\n\n    if df_chart.empty:\n        raise ValueError(\"DataFrame final do gráfico está vazio\")\n\n    return df_chart\n\n\ndef build_plotly_price_dataframe(\n    price_snapshots: pd.DataFrame,\n    ranking_payload: list[dict],\n    price_field: str = \"Adj Close\"\n) -> pd.DataFrame:\n    \"\"\"\n    Constrói o DataFrame final para visualização no Plotly.\n\n    Retorna um DataFrame em formato longo (long-form), contendo:\n    - ticker\n    - date\n    - adj_close\n    - variação percentual ponto-a-ponto\n    - FR\n    - FR_rank\n    \"\"\"\n\n    if price_snapshots.empty:\n        raise ValueError(\"price_snapshots vazio\")\n\n    if not ranking_payload:\n        raise ValueError(\"ranking_payload vazio\")\n\n    # ------------------------------------------------------------------\n    # 1. Ativos selecionados no ranking\n    # ------------------------------------------------------------------\n    ranking_df = pd.DataFrame(ranking_payload)[[\"ticker\", \"FR\", \"FR_rank\"]]\n    selected_tickers = ranking_df[\"ticker\"].tolist()\n\n    # ------------------------------------------------------------------\n    # 2. Extrair apenas Adj Close dos ativos selecionados\n    # ------------------------------------------------------------------\n    adj_close = (\n        price_snapshots\n        .loc[:, (price_field, selected_tickers)]\n        .copy()\n    )\n\n    # ------------------------------------------------------------------\n    # 3. Flatten: Date vira coluna, ticker vira coluna\n    # ------------------------------------------------------------------\n    adj_close.columns = adj_close.columns.droplevel(0)\n    adj_close = adj_close.reset_index()  # Date vira coluna\n\n    long_df = adj_close.melt(\n        id_vars=\"Date\",\n        var_name=\"ticker\",\n        value_name=\"adj_close\"\n    )\n\n    # ------------------------------------------------------------------\n    # 4. Ordenação temporal e cálculo da variação percentual\n    # ------------------------------------------------------------------\n    long_df = long_df.sort_values([\"ticker\", \"Date\"])\n\n    long_df[\"pct_change\"] = (\n        long_df\n        .groupby(\"ticker\")[\"adj_close\"]\n        .pct_change()\n        .mul(100)\n    )\n\n    # ------------------------------------------------------------------\n    # 5. Enriquecimento com FR e FR_rank\n    # ------------------------------------------------------------------\n    long_df = long_df.merge(\n        ranking_df,\n        on=\"ticker\",\n        how=\"left\"\n    )\n\n    return long_df\n    \n    \n    \ndef add_percent_change_for_hover(\n    df_prices: pd.DataFrame,\n    prefix: str = \"pct_\"\n) -> pd.DataFrame:\n    \"\"\"\n    Adiciona colunas de variação percentual ponto-a-ponto para uso em hover.\n\n    Parâmetros\n    ----------\n    df_prices : pd.DataFrame\n        DataFrame com:\n        - índice = ticker\n        - colunas = datas (ordenadas cronologicamente)\n        - valores = preços ajustados (Adj Close)\n\n    prefix : str\n        Prefixo das colunas de variação percentual.\n\n    Retorno\n    -------\n    pd.DataFrame\n        Mesmo DataFrame, com colunas adicionais no formato:\n        pct_<data>\n    \"\"\"\n\n    if df_prices.empty:\n        raise ValueError(\"DataFrame vazio\")\n\n    # garantir ordenação temporal das colunas\n    df_prices = df_prices.copy()\n    df_prices = df_prices.sort_index(axis=1)\n\n    pct_change = df_prices.pct_change(axis=1) * 100\n    pct_change.columns = [f\"{prefix}{col}\" for col in pct_change.columns]\n\n    return pd.concat([df_prices, pct_change], axis=1)\n    \ndef build_plotly_payload(df_chart: pd.DataFrame) -> list[dict]:\n    \"\"\"\n    Constrói o payload JSON para consumo direto pelo Plotly JS.\n\n    Retorna uma lista de traces, um por ativo.\n    \"\"\"\n\n    payload = []\n\n    for ticker, row in df_chart.iterrows():\n        prices = row.values\n        dates = df_chart.columns.astype(str).tolist()\n\n        # Variação percentual em relação ao primeiro ponto\n        base_price = prices[0]\n        pct_change = ((prices / base_price) - 1.0) * 100\n\n        trace = {\n            \"type\": \"scatter\",\n            \"mode\": \"lines+markers\",\n            \"name\": ticker,\n            \"x\": dates,\n            \"y\": prices.tolist(),\n            \"customdata\": pct_change.round(2).tolist(),\n            \"hovertemplate\": (\n                \"<b>%{fullData.name}</b><br>\"\n                \"Data: %{x}<br>\"\n                \"Preço: %{y:.2f}<br>\"\n                \"Variação: %{customdata:.2f}%\"\n                \"<extra></extra>\"\n            ),\n        }\n\n        payload.append(trace)\n\n    return payload\n\n\ndef extract_latest(prices: pd.DataFrame,\n                   price_field: str = \"Adj Close\",\n                   indicator_fields: Optional[List[str]] = None) -> pd.DataFrame:\n    \"\"\"\n    Extrai o último registro por ticker a partir do DataFrame 'prices' que tem\n    MultiIndex nas colunas com níveis ['Field','Ticker'].\n    Retorna DataFrame com colunas: ['Ticker', price_field, <indicator_fields>].\n    \"\"\"\n    if not isinstance(prices.columns, pd.MultiIndex):\n        raise ValueError(\"extract_latest: espera columns como MultiIndex com níveis ['Field','Ticker'].\")\n\n    # lista de fields disponíveis e tickers (garantir strings)\n    fields_available = list(prices.columns.get_level_values('Field').unique())\n    tickers = prices.columns.get_level_values('Ticker').unique().astype(str)\n\n    # detectar STOP_ATR se indicator_fields não fornecido\n    if indicator_fields is None:\n        indicator_fields = [f for f in fields_available if str(f).upper().startswith(\"STOP_ATR\")]\n    else:\n        # filtrar somente os que existem\n        indicator_fields = [f for f in indicator_fields if f in fields_available]\n\n    needed_fields = [price_field] + indicator_fields\n\n    series_list = []\n    for fld in needed_fields:\n        if fld in fields_available:\n            df_field = prices.xs(fld, axis=1, level='Field')\n            # garantir DataFrame (caso particular)\n            if isinstance(df_field, pd.Series):\n                df_field = df_field.to_frame().T\n\n            # se não houver linhas (por algum motivo), criar Series de NaNs\n            if df_field.shape[0] == 0:\n                s = pd.Series(index=tickers, data=np.nan, name=str(fld))\n            else:\n                s = df_field.iloc[-1]                # último candle\n                # garantir que o índice seja string e correspondente a 'tickers'\n                s.index = s.index.astype(str)\n                s = s.reindex(tickers)              # alinha na mesma ordem / mesmo índice\n                s.name = str(fld)\n        else:\n            # field ausente -> série de NaNs\n            s = pd.Series(index=tickers, data=np.nan, name=str(fld))\n\n        series_list.append(s)\n\n    # concatenar séries (todas com mesmo índice: tickers)\n    df_latest = pd.concat(series_list, axis=1)\n    df_latest.index.name = 'Ticker'\n    df_latest = df_latest.reset_index()  # torna 'Ticker' coluna\n    return df_latest"
}
```

## Assistant

<thinking>
Now I have a comprehensive understanding of the project. Let me analyze the issue with `run_pipeline` being called twice and then suggest a proper refactoring.

The flow is:
1. User clicks Run → `fr_chart.js.runPipeline()` → `/api/fr-price-series` endpoint
   - Calls `init()` (if no prices cached)
   - Calls `run_pipeline()` → returns `result` with `ranking` and `charts.price_snapshots`
   - Uses `price_snapshots` for the chart
   - Returns Plotly payload for Chart 1

2. Frontend calls `/api/ranking` endpoint
   - Gets `price_repository.current_reference_date()`
   - Calls `run_pipeline()` again (redundant!) → returns `result["ranking"]`

So `run_pipeline` is being executed twice: once in `/fr-price-series` and again in `/api/ranking`, even though the ranking data was already computed in the first call. I should either cache the pipeline result in a repository like `PriceRepository` does, or split `run_pipeline` into separate functions for building the ranking and computing the scoring.

Looking at what `run_pipeline` actually does, it handles a lot: resolving trading dates, extracting price snapshots, calculating relative strength, building the ranking, enriching the data, computing risk/return metrics, and sanitizing everything for JSON. The issue is that `/fr-price-series` needs the price snapshots and ranking to filter tickers, while `/api/ranking` only needs the ranking itself, but both are running the full pipeline. I think the cleanest approach would be to introduce a `RankingRepository` that caches the computed ranking data, similar to how `PriceRepository` works.

Organizing the code structure...

I'm thinking the cleanest solution is to split `run_pipeline` into two focused functions: one that handles the ranking computation (scoring, ranking, enrichment) which gets cached in a new `RankingRepository`, and another for chart building. Then the routes can call the cached ranking function and build their specific payloads from it, avoiding redundant computation across endpoints.

Now I'm working through the actual implementation—defining a `build_ranking_result` function that encapsulates steps 5-9 of the pipeline, returning the summary, ranking list, and price snapshots so both the chart route and the ranking API endpoint can use the cached result. This approach eliminates the redundant pipeline execution. Now I need to check the main.py and config.py files to understand the current setup and ensure the refactoring fits cleanly into the existing structure.
</thinking>

Agora deixa eu ver os arquivos restantes para ter o quadro completo.

**Tool Call: Read file `main.py`**
Status: Completed

```json
{
  "Text": "from fastapi import FastAPI, Query, Request\nfrom fastapi.templating import Jinja2Templates\nfrom fastapi.staticfiles import StaticFiles\n\n\nfrom pydantic import BaseModel, Field\nfrom typing import Optional\nfrom datetime import date\n\nfrom app.core import config\nfrom app.core.pipeline import run_pipeline\n\nfrom app.api.routes import router as api_router\n\n# =========================================================\n# FastAPI app\n# =========================================================\n\napp = FastAPI(\n    title=\"Trend Following API\",\n    description=\"API para análise de força relativa e ranking de ativos da B3\",\n    version=\"0.1.0\",\n)\napp.mount(\"/static\", StaticFiles(directory=\"ui/static\"), name=\"static\")\ntemplates = Jinja2Templates(directory=\"ui/templates\")\n\n\n# ------------------------------------------------------------------\n# Registro dos routers\n# ------------------------------------------------------------------\napp.include_router(api_router, prefix=\"/api\")\n\n\n# =========================================================\n# Endpoints\n# =========================================================\n\n@app.get(\"/\")\ndef index(request: Request):\n    return templates.TemplateResponse(\n        \"index.html\",\n        {\"request\": request}\n    )\n    \n@app.get(\"/health\")\ndef health_check():\n    \"\"\"\n    Endpoint simples para verificação de status.\n    \"\"\"\n    return {\"status\": \"ok\"}\n\n\n@app.get(\"/run\")\ndef run_trend_following(reference_date: Optional[str] = Query(\n    default=None, description=\"Data de referência no formato YYYY-MM-DD\")):\n    \"\"\"\n    Executa o pipeline completo e retorna ranking e summary.\n    \"\"\"\n\n    result = run_pipeline(reference_date=reference_date)\n\n    return {\n        \"summary\": result[\"summary\"],\n        \"ranking\": result[\"ranking\"],\n        \"metadata\": result.get(\"metadata\", {}),\n        \"charts\": result.get(\"charts\", {})\n    }\n"
}
```

**Tool Call: Read file `app\config.py`**
Status: Completed

```json
{
  "Text": "\"\"\"\nconfig.py\n\nParâmetros globais de configuração do sistema.\nContém apenas constantes e valores default.\n\"\"\"\n\n# ===============================\n# Universo de ativos (BRAPI)\n# ===============================\nMIN_PRICE = 5.0\nMIN_VOLUME = 1_000_000\nEXCLUDE_SUFFIXES = (\"11\", \"32\")\n\n# ===============================\n# Horizonte temporal\n# ===============================\nANALYSIS_MONTHS = 6\nDATE_FORMAT = \"%Y-%m-%d\"\n\n# ===============================\n# Indicadores técnicos\n# ===============================\nMA_WINDOW = 20\n\nBOLLINGER_WINDOW = 20\nBOLLINGER_STD = 2\n\nMACD_FAST = 12\nMACD_SLOW = 26\nMACD_SIGNAL = 9\n\nATR_WINDOW = 14\nATR_MULTIPLIER = 1.5\n\n# ===============================\n# Scoring e Ranking\n# ===============================\nFR_SCALE = (0, 100)\nMIN_FR = 80.0\nTOP_N = 10\n\n# ===============================\n# Infraestrutura\n# ===============================\nREQUEST_TIMEOUT = 30\nENABLE_CACHE = False\n"
}
```

**Tool Call: List the `C:\Users\Bruno\trend\ui\static` directory's contents**
Status: Completed

# Folders:
trend\ui\static\css
trend\ui\static\js


**Tool Call: List the `C:\Users\Bruno\trend\ui\static\js` directory's contents**
Status: Completed


# Files:
trend\ui\static\js\candlechart.js
trend\ui\static\js\fr_chart.js
trend\ui\static\js\table.js


**Tool Call: Read file `ui\static\js\fr_chart.js`**
Status: Completed

```json
{
  "Text": "async function runPipeline() {\n    const dateInput = document.getElementById(\"referenceDate\").value;\n\n    let url = \"/api/fr-price-series\";\n    if (dateInput) {\n        url += `?reference_date=${dateInput}`;\n    }\n\n    try {\n        const response = await fetch(url);\n        if (!response.ok) {\n            throw new Error(\"Erro ao obter dados do backend\");\n        }\n\n        const result = await response.json();\n\n        Plotly.newPlot(\n            \"chart\",\n            result.data,\n            result.layout,\n            { responsive: true }\n        );\n\t\t\n\t\t// após Plotly.newPlot(...)\n\t\tif (typeof window.renderRankingTable === \"function\") {\n\t\t\tif (result && result.ranking) {\n\t\t\t\twindow.renderRankingTable(result.ranking);\n\t\t\t} else {\n\t\t\t\t// fallback: só chamar fetch se não houver ranking no response\n\t\t\t\tif (typeof window.fetchAndRenderRankingTable === \"function\") {\n\t\t\t\t\twindow.fetchAndRenderRankingTable(dateInput);\n\t\t\t\t}\n\t\t\t}\n\t\t}\t\t\n\n    } catch (error) {\n        console.error(error);\n        alert(\"Erro ao executar o pipeline.\");\n    }\t\n\t\n}\n"
}
```

**Tool Call: Read file `ui\static\js\table.js`**
Status: Completed

```json
{
  "Text": "// /static/js/fr_table.js\n// Renderizador de tabela usando Grid.js — somente tabela (sem gráfico)\n\n// Fetch + render a partir do endpoint /api/ranking\nasync function fetchAndRenderRankingTable(referenceDate = '') {\n    const url = `/api/ranking${referenceDate ? '?reference_date=' + encodeURIComponent(referenceDate) : ''}`;\n    try {\n        const resp = await fetch(url);\n        if (!resp.ok) {\n            console.error('Erro ao obter ranking:', resp.status, resp.statusText);\n            renderEmptyTable('Erro ao obter dados.');\n            return;\n        }\n        const data = await resp.json();\n        renderRankingTable(data);\n    } catch (err) {\n        console.error('Erro ao buscar ranking:', err);\n        renderEmptyTable('Erro ao obter dados2.');\n    }\n}\n\n// Renderiza um array de objetos (records) usando Grid.js\nfunction renderRankingTable(data) {\n    const container = document.getElementById('table');\n    if (!container) {\n        console.warn('Container #table não encontrado no DOM.');\n        return;\n    }\n    container.innerHTML = ''; // limpa\n\n    if (!data || !Array.isArray(data) || data.length === 0) {\n        renderEmptyTable('Nenhum dado disponível.');\n        return;\n    }\n\n    // Normaliza chaves (ordem fixa: ticker primeiro se existir)\n    const first = data[0];\n    const keys = Object.keys(first);\n\n    // opcional: força ordem útil — coloca 'ticker' ou 'Ticker' primeiro se existir\n    const tickerKeyIndex = keys.findIndex(k => k.toLowerCase() === 'ticker');\n    if (tickerKeyIndex > 0) {\n        const [tk] = keys.splice(tickerKeyIndex, 1);\n        keys.splice(0, 0, tk);\n    }\n\n    // Constrói os dados para Grid.js (array de arrays)\n    const gridData = data.map(row => keys.map(k => formatCellValue(row[k])));\n\n    // Colunas para Grid.js\n    const columns = keys.map(k => ({\n        id: k,\n        name: k,\n        // Você pode adicionar formatter aqui se quiser formatar números\n    }));\n\n    // Renderiza Grid.js\n    const grid = new gridjs.Grid({\n        columns: columns,\n        data: gridData,\n        sort: true,\n        pagination: {\n            enabled: true,\n            limit: 20\n        },\n        resizable: true,\n        fixedHeader: true,\n        style: {\n            // usa classes CSS do tema; cabeçalho customizado via CSS no index.html\n        }\n    });\n\n    grid.render(container);\n\n    // Adiciona highlight de linha via event delegation\n    // (usa delegated click para encontrar .gridjs-tr)\n    container.addEventListener('click', function (ev) {\n        const tr = ev.target.closest('.gridjs-tr');\n        if (!tr) return;\n        // ignora cabeçalho\n        if (tr.classList.contains('gridjs-head')) return;\n\n        // remove seleção anterior\n        const prev = container.querySelectorAll('.gridjs-tr.selected');\n        prev.forEach(r => r.classList.remove('selected'));\n\n        // aplica seleção\n        tr.classList.add('selected');\n\n        // opcional: expõe evento customizado com os dados da linha\n        const cells = Array.from(tr.querySelectorAll('.gridjs-td')).map(td => td.textContent.trim());\n        const rowObj = {};\n        keys.forEach((k, idx) => rowObj[k] = cells[idx]);\n        // dispara evento custom no container (ou use console.log)\n        const evt = new CustomEvent('fr:rowSelected', { detail: rowObj });\n        container.dispatchEvent(evt);\n\t\t\n\t\t\n\t\t\n    }, false);\n}\n\n// formata valor de célula de forma simples\nfunction formatCellValue(v) {\n    if (v === null || typeof v === 'undefined') return '';\n    // se for número, formata com 2 decimais (mas mantém tipo string para exibição)\n    if (typeof v === 'number' && isFinite(v)) {\n        return Number.isInteger(v) ? v.toString() : v.toFixed(2);\n    }\n    // se for objeto/array, stringify de forma simples\n    if (typeof v === 'object') return JSON.stringify(v);\n    return String(v);\n}\n\nfunction renderEmptyTable(message) {\n    const container = document.getElementById('table');\n    if (!container) return;\n    container.innerHTML = `<p>${message}</p>`;\n}\n\n// Expõe funções globalmente para que fr_chart.js possa chamar quando desejar\nwindow.fetchAndRenderRankingTable = fetchAndRenderRankingTable;\nwindow.renderRankingTable = renderRankingTable;\n\n// Auto-load ao carregar a página (sem referência de data)\n// document.addEventListener('DOMContentLoaded', function () {\n    // Carrega tabela padrão sem reference_date (você pode remover se preferir carregar somente via chamada explícita)\n    // fetchAndRenderRankingTable();\n// });"
}
```

## Assistant

<thinking>
Now I have a comprehensive understanding of the entire project. Let me analyze the problem and create a detailed refactoring plan.

**The Core Problem:**

`run_pipeline` is called twice:
1. In `/api/fr-price-series` → to get `price_snapshots` for the chart AND `ranking` for filtering tickers
2. In `/api/ranking` → to get `ranking` for the table

This is inefficient because all the computation (date resolution, scoring, ranking, enrichment, indicators) is done twice.

**The Fix:**

Looking at `fr_chart.js`, I can see it already has a smart approach: when `/api/fr-price-series` returns data, it checks `if (result && result.ranking)` and calls `window.renderRankingTable(result.ranking)` directly, bypassing the need to call `/api/ranking` at all! But the current `/api/fr-price-series` endpoint does NOT return `ranking` in its response - it only returns `{data, layout}` for Plotly.
 
I'm seeing two viable paths forward. The first is to modify `/api/fr-price-series` to include `ranking` in its response since the frontend already expects this pattern. The second is to add caching so the second call reuses the first computation. The best approach combines both: I'll restructure the endpoints to return ranking data from the price series endpoint while also implementing a cache layer to handle any fallback scenarios. I'm renaming `pipeline.py` to `ranking_pipeline.py` and the `run_pipeline` function to `build_ranking_result`, then updating the routes to use the ranking cache and include ranking data in the fr-price-series response. I also need to remove the orphan `/run` endpoint from main.py that still references the old function name.

Looking at the frontend logic in `fr_chart.js`, I see it checks if ranking exists in the response first, and only falls back to a separate fetch if it's missing—so embedding the ranking directly in the fr-price-series response eliminates the double execution and aligns perfectly with what the frontend already expects.
</thinking>

Agora tenho uma visão completa do projeto. Vou analisar o problema com precisão antes de propor a refatoração.

---

## Diagnóstico

O problema tem **duas causas distintas**, não apenas uma:

### Causa 1 — `run_pipeline` executado duas vezes no backend

```C:\Users\Bruno\trend\app\api\routes.py#L42-L55
# /api/fr-price-series → chama run_pipeline(...)
result = run_pipeline(prices=prices, reference_date=reference_date)

# /api/ranking → também chama run_pipeline(...)
result = run_pipeline(prices=prices, reference_date=reference_date)
```

Todo o trabalho pesado (resolução de datas, scoring de FR, ranking, merge, enriquecimento, indicadores de risco/retorno) é **refeito do zero** para servir a tabela, mesmo que já tenha sido calculado para o gráfico.

### Causa 2 — O frontend já tem a solução, mas o backend não entrega os dados

```C:\Users\Bruno\trend\ui\static\js\fr_chart.js#L16-L24
if (result && result.ranking) {
    window.renderRankingTable(result.ranking);   // ← já usa ranking inline
} else {
    // fallback: só chamar fetch se não houver ranking no response
    if (typeof window.fetchAndRenderRankingTable === "function") {
        window.fetchAndRenderRankingTable(dateInput); // ← dispara /api/ranking
    }
}
```

`fr_chart.js` já prevê receber `ranking` embutido na resposta de `/api/fr-price-series`, mas o endpoint só devolve `{data, layout}` — forçando o fallback que chama `/api/ranking`, que por sua vez executa `run_pipeline` de novo.

---

## Raiz do problema arquitetural

`run_pipeline` acumula responsabilidades demais. Ele faz **scoring → ranking → enriquecimento → sanitização → montagem do payload de gráfico**, mas seus resultados não são cacheados. Cada endpoint que precisa de qualquer parte disso re-executa tudo.

---

## Refatoração proposta

A ideia central é: **computar uma vez, cachear, servir em múltiplos pontos.**

### 1. Dividir `pipeline.py` em dois módulos com responsabilidades bem definidas

**`app/core/ranking_pipeline.py`** — o que hoje é `run_pipeline`, renomeado e isolado:

```C:\Users\Bruno\trend\app\core\ranking_pipeline.py#L1-10
# Responsabilidade única: executar os passos 5–9
# Entrada: prices (df já com indicadores) + reference_date
# Saída: dict com "summary", "ranking" (list[dict]) e "price_snapshots" (df)
def build_ranking_result(prices, reference_date) -> dict: ...
```

**`app/core/chart_builders.py`** (pasta `charts/` já existe vazia) — o que hoje está espalhado nas routes:

```C:\Users\Bruno\trend\app\charts\chart_builders.py#L1-10
# Responsabilidade única: transformar dados já calculados em payloads Plotly
def build_fr_chart_payload(price_snapshots, ranking) -> dict: ...
def build_candle_chart_payload(df_ticker, ticker) -> dict: ...
```

### 2. Criar `RankingRepository` para cachear o resultado do pipeline

Espelhando o `PriceRepository` já existente:

```C:\Users\Bruno\trend\app\core\ranking_repository.py#L1-10
class RankingRepository:
    def has(reference_date) -> bool
    def get(reference_date) -> dict       # retorna {summary, ranking, price_snapshots}
    def set(reference_date, result) -> None

ranking_repository = RankingRepository()  # singleton
```

### 3. Reformular os endpoints — um só pipeline por request

```C:\Users\Bruno\trend\app\api\routes.py#L1-10
# /api/fr-price-series
# 1. init prices se necessário        → price_repository
# 2. build_ranking_result se necessário → ranking_repository (executa 1x)
# 3. build_fr_chart_payload()
# 4. retorna {data, layout, ranking}   ← inclui ranking na resposta!

# /api/ranking
# 1. lê reference_date do price_repository
# 2. lê result do ranking_repository   ← zero recomputação
# 3. retorna result["ranking"]
```

---

## Estrutura final das responsabilidades

| Arquivo | Responsabilidade |
|---|---|
| `core/init.py` | Passos 1–4: universo de ativos, download, indicadores |
| `core/ranking_pipeline.py` | Passos 5–9: datas, scoring, ranking, enriquecimento |
| `core/price_repository.py` | Cache do `prices` (já existe) |
| `core/ranking_repository.py` | **Novo**: cache do `build_ranking_result` |
| `charts/chart_builders.py` | **Novo**: montagem dos payloads Plotly (gráfico 1 e 2) |
| `api/routes.py` | Orquestração dos endpoints — sem lógica de negócio inline |
| `main.py` | Apenas registro do app/router e endpoint de health/index |

---

## Benefícios imediatos

1. **`run_pipeline` (futuro `build_ranking_result`) executa exatamente uma vez** por `reference_date` — resultado cacheado no `RankingRepository`
2. **`/api/fr-price-series` passa a devolver `ranking` na resposta** — o frontend usa o caminho já implementado em `fr_chart.js` e nunca mais precisa chamar `/api/ranking` por padrão
3. **`/api/ranking` torna-se leve** — apenas leitura do cache, zero recomputação
4. **`/api/candlechart` não muda** — já usa `price_repository` corretamente
5. **`app/charts/`** (hoje vazio) ganha uma razão de existir

---

Quer que eu implemente essa refatoração? Posso fazer tudo de uma vez ou em etapas — me diga como prefere.

## User

Sim, implemente essa refatoração por etapas, mencionando primeiro o que será feito. Renomeie essa função 'run_pipeline', se ela ainda existir após a refatoração; o nome não condiz com as responsabilidades definidas nela.

## Assistant

<thinking>
The user wants me to implement the refactoring in stages, mentioning what will be done first. Let me plan the stages carefully:

**Stage 1: Create `RankingRepository`**
- Create `app/core/ranking_repository.py`

**Stage 2: Create `ranking_pipeline.py` (renamed from `pipeline.py`)**
- Create `app/core/ranking_pipeline.py` with the function renamed from `run_pipeline` to `build_ranking_result`
- Keep `pipeline.py` around or deprecate it

**Stage 3: Create `chart_builders.py`**


- Create `app/charts/chart_builders.py` with functions to build the FR chart and candle chart payloads

**Stage 4: Update `routes.py`**
- Use `ranking_repository` and `build_ranking_result`
- Return `ranking` in `/api/fr-price-series` response

**Stage 5: Clean up `main.py`**
- Remove orphan `/run` endpoint

**Stage 6: Remove/deprecate old `pipeline.py`**

Now I'm refining the plan. I'll create `RankingRepository` first, then rename `pipeline.py` to `ranking_pipeline.py` with the main function renamed to `build_ranking_result`. After that, I'll extract the chart building logic into separate functions and update the routes to use these new modules.

Let me start by reviewing what `pipeline.py` actually does — it orchestrates the entire ranking workflow from extracting latest prices through calculating risk/return indicators and returning the final result with summary, ranking data, and price snapshots for charts.

Then in `routes.py`, the `/api/fr-price-series` endpoint takes those price snapshots and builds a Plotly chart payload, while `/api/candlechart` has a bunch of inline chart logic that I need to extract into its own builder function.

So I'm identifying two chart builders to extract: one for the French price series visualization and another for candlestick charts. Now I'm starting to implement the refactoring by creating a repository class...

Defining the ranking repository class... Completing the error handling for the get method, then implementing set to validate the result is a dictionary before storing it, and a clear method to reset the store. I'm also instantiating a global ranking_repository instance for use throughout the application. Now moving on to rename the pipeline function and extract the chart building logic.

For the chart builders, I need two functions: one that takes price snapshots and ranking data to filter tickers and construct the Plotly payload with data and layout, and another that builds candlestick chart traces from ticker data. Then I'll update the routes to use the repository for caching, call the pipeline and chart builders appropriately, and clean up the main file. Now I'm ready to start implementing these changes across all five stages, updating the routes to use the new repositories and chart builders, and cleaning up the orphaned endpoints in the main file.
</thinking>

## Plano das etapas

Antes de escrever qualquer código, aqui está o que será feito em cada etapa e **por quê**:

| Etapa | O que | Por quê |
|---|---|---|
| **1** | Criar `app/core/ranking_repository.py` | Cache do resultado do pipeline — pré-requisito para eliminar a dupla execução |
| **2** | Criar `app/core/ranking_pipeline.py` com `build_ranking_result` e deletar `pipeline.py` | Renomear a função + isolar a responsabilidade de scoring/ranking/enriquecimento em seu próprio módulo |
| **3** | Criar `app/charts/chart_builders.py` | Tirar a lógica de montagem de payload Plotly das routes, que hoje vive inline |
| **4** | Reescrever `app/api/routes.py` | Orquestrar tudo sem lógica de negócio inline; `/fr-price-series` passa a retornar `ranking`; `/ranking` vira leitura de cache |
| **5** | Limpar `main.py` | Remover o endpoint `/run` órfão e o import de `run_pipeline` que não existirá mais |

---

### Etapa 1 — `RankingRepository`

**Tool Call: app\core\ranking_repository.py**
Status: Completed

Diff: C:\Users\Bruno\trend\app\core\ranking_repository.py
```
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

```


## Assistant

---

### Etapa 2 — `ranking_pipeline.py` com `build_ranking_result` + remoção de `pipeline.py`

`run_pipeline` vira `build_ranking_result`. O retorno também muda: em vez de enterrar os `price_snapshots` dentro de `charts`, ele os expõe como chave de primeiro nível, que é o contrato esperado pelo novo `RankingRepository`.

**Tool Call: app\core\ranking_pipeline.py**
Status: Completed

Diff: C:\Users\Bruno\trend\app\core\ranking_pipeline.py
```
"""
ranking_pipeline.py

Pipeline de scoring, ranking e enriquecimento de ativos (passos 5–9).

Responsabilidades:
- resolver datas de pregão válidas a partir de datas teóricas
- extrair snapshots de preço por data
- calcular Força Relativa (scoring)
- ranquear e filtrar ativos
- enriquecer o ranking com metadados, indicadores e métricas de risco/retorno
- sanitizar e estruturar o payload final

Este módulo NÃO:
- baixa dados de mercado
- calcula indicadores técnicos no histórico completo
- monta payloads Plotly
- conhece endpoints ou detalhes de HTTP
"""

from typing import Any, Dict

import numpy as np
import pandas as pd

import app.config as config
from app.data.market_data import (
    enrich_with_metadata_and_52w_high,
    generate_theoretical_dates,
)
from app.data.preprocessing import (
    extract_latest,
    extract_price_snapshots,
    flatten_snapshot_for_scoring,
    resolve_to_trading_dates,
)
from app.finance.indicators import calculate_risk_return_indicators
from app.services.ranking import build_ranking
from app.services.scoring import calculate_relative_strength


def build_ranking_result(
    prices: pd.DataFrame,
    reference_date: str | None = None,
) -> Dict[str, Any]:
    """
    Executa os passos 5–9 do pipeline: scoring → ranking → enriquecimento.

    Assume que ``prices`` já foi:
    - baixado e normalizado (passo 1–3, responsabilidade de ``init``)
    - enriquecido com indicadores técnicos no histórico completo (passo 4)

    Parâmetros
    ----------
    prices : pd.DataFrame
        DataFrame MultiIndex (Field, Ticker) com histórico de preços e
        indicadores técnicos já calculados.
    reference_date : str | None
        Data de referência no formato YYYY-MM-DD.
        Se None, usa a data de hoje.

    Retorno
    -------
    dict com as chaves:
    - ``"summary"``         : dict com métricas resumidas da execução
    - ``"ranking"``         : list[dict] dos ativos ranqueados e enriquecidos,
                              prontos para serialização JSON
    - ``"price_snapshots"`` : pd.DataFrame MultiIndex com snapshots de preço
                              nas datas resolvidas (consumido pelo chart builder)

    Retornos antecipados (sem erro):
    - Nenhum ativo pontuado  → ranking e price_snapshots vazios
    - Nenhum ativo no ranking → ranking vazio, price_snapshots disponível
    """

    # ------------------------------------------------------------------
    # 5. Extração do último valor de indicadores por ticker
    # ------------------------------------------------------------------
    df_latest = extract_latest(prices, price_field="Adj Close", indicator_fields=None)
    df_latest["Ticker"] = df_latest["Ticker"].astype(str).str.strip().str.upper()

    # ------------------------------------------------------------------
    # 6. Resolução das datas válidas e extração de snapshots
    # ------------------------------------------------------------------
    theoretical_dates = generate_theoretical_dates(reference_date)

    trading_dates = resolve_to_trading_dates(
        prices.index,
        theoretical_dates,
    )

    price_snapshots = extract_price_snapshots(
        prices,
        trading_dates,
        price_field="Adj Close",
    )

    # flat: índice = ticker, colunas = p0..pN (preços nas datas selecionadas)
    df_flat = flatten_snapshot_for_scoring(price_snapshots)

    # ------------------------------------------------------------------
    # 7. Scoring — Força Relativa (FR)
    # ------------------------------------------------------------------
    scored = calculate_relative_strength(df_flat)

    if scored.empty:
        return {
            "summary": {"message": "Nenhum ativo pontuado"},
            "ranking": [],
            "price_snapshots": price_snapshots,
        }

    # ------------------------------------------------------------------
    # 8. Ranking — ordenação, percentil e filtro
    # ------------------------------------------------------------------
    ranking_result = build_ranking(
        df=scored,
        score_column="FR",
        min_score=config.MIN_FR,
        top_n=config.TOP_N,
        payload_fields=["FR", "FR_rank"],
    )

    if not ranking_result["payload"]:
        return {
            "summary": {"message": "Nenhum ativo passou no ranking"},
            "ranking": [],
            "price_snapshots": price_snapshots,
        }

    # ------------------------------------------------------------------
    # 9. Pós-ranking: merge com últimos valores + metadados + risco/retorno
    # ------------------------------------------------------------------
    df_ranked = pd.DataFrame(ranking_result["payload"])
    df_ranked["ticker"] = df_ranked["ticker"].astype(str).str.strip().str.upper()

    df_latest = df_latest.rename(columns={"Ticker": "ticker"})

    df_ranked = df_ranked.merge(
        df_latest,
        on="ticker",
        how="left",
        validate="m:1",
    )

    df_enriched = enrich_with_metadata_and_52w_high(
        df=df_ranked,
        ticker_column="ticker",
    )

    df_final = calculate_risk_return_indicators(
        df=df_enriched,
        price_col="Adj Close",
        stop_col="STOP_ATR_14_1.5",
        high_52w_col="high_52w",
    )

    # ------------------------------------------------------------------
    # 10. Sanitização para serialização JSON
    # ------------------------------------------------------------------
    df_clean = df_final.copy()
    df_clean.replace([np.inf, -np.inf], np.nan, inplace=True)

    num_cols = df_clean.select_dtypes(include=[np.number])
    non_finite_mask = ~np.isfinite(num_cols)
    if non_finite_mask.any().any():
        bad_cols = non_finite_mask.any()[non_finite_mask.any()].index.tolist()
        print(f"[ranking_pipeline] Colunas com valores não finitos: {bad_cols}")

    ranking_records = df_clean.to_dict(orient="records")

    # Substitui float não-finitos por None (JSON-safe)
    for row in ranking_records:
        for key, value in row.items():
            if isinstance(value, float) and not np.isfinite(value):
                row[key] = None

    # ------------------------------------------------------------------
    # 11. Montagem do retorno
    # ------------------------------------------------------------------
    summary = {
        "scored_assets": len(scored),
        "ranked_assets": len(ranking_records),
        "reference_date": reference_date,
    }

    return {
        "summary": summary,
        "ranking": ranking_records,
        "price_snapshots": price_snapshots,
    }

```


## Assistant

Agora remove o `pipeline.py` original:

**Tool Call: Delete “`C:\Users\Bruno\trend\app\core\pipeline.py`”**
Status: Completed

Deleted C:\Users\Bruno\trend\app\core\pipeline.py

## Assistant

---

### Etapa 3 — `chart_builders.py`

Toda a lógica de montagem de payload Plotly que hoje vive inline nas routes vai para cá:

**Tool Call: app\charts\chart_builders.py**
Status: Completed

Diff: C:\Users\Bruno\trend\app\charts\chart_builders.py
```
"""
chart_builders.py

Responsável pela montagem de payloads Plotly prontos para consumo pelo frontend.

Responsabilidades:
- receber DataFrames já calculados (preços, indicadores, ranking)
- estruturar traces e layouts no formato esperado pelo Plotly JS
- retornar dicts serializáveis (JSON-safe)

Este módulo NÃO:
- baixa dados de mercado
- calcula indicadores técnicos
- executa scoring ou ranking
- conhece endpoints ou detalhes de HTTP
"""

from typing import Any, Dict, List

import pandas as pd

import app.config as config
from app.data.preprocessing import build_plotly_payload, build_price_matrix_for_chart

# ===========================================================================
# Gráfico 1 — Força Relativa (linha por ativo ranqueado)
# ===========================================================================


def build_fr_chart_payload(
    price_snapshots: pd.DataFrame,
    ranking: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Monta o payload Plotly para o gráfico de validação da Força Relativa.

    Parâmetros
    ----------
    price_snapshots : pd.DataFrame
        DataFrame MultiIndex (Field, Ticker) com snapshots de preço
        nas datas resolvidas, produzido por build_ranking_result.
    ranking : list[dict]
        Lista de ativos ranqueados retornada por build_ranking_result,
        cada item contendo ao menos as chaves "ticker" e "FR_rank".

    Retorno
    -------
    dict com as chaves:
    - "data"   : list[dict] — traces Plotly
    - "layout" : dict       — configuração do layout Plotly
    """

    if price_snapshots is None or (
        hasattr(price_snapshots, "empty") and price_snapshots.empty
    ):
        raise ValueError("price_snapshots está vazio ou None")

    if not ranking:
        raise ValueError("ranking está vazio")

    # ------------------------------------------------------------------
    # Filtra tickers que atendem ao critério mínimo de FR_rank
    # ------------------------------------------------------------------
    selected_tickers = [
        item["ticker"] for item in ranking if item.get("FR_rank", 0) >= config.MIN_FR
    ]

    if not selected_tickers:
        raise ValueError(
            f"Nenhum ativo atende ao critério mínimo de FR_rank >= {config.MIN_FR}"
        )

    # ------------------------------------------------------------------
    # Monta matriz de preços (ticker × datas) para o gráfico
    # ------------------------------------------------------------------
    df_chart = build_price_matrix_for_chart(
        price_snapshots=price_snapshots,
        selected_tickers=selected_tickers,
        price_field="Adj Close",
    )

    # ------------------------------------------------------------------
    # Converte para traces Plotly
    # ------------------------------------------------------------------
    plotly_data = build_plotly_payload(df_chart)

    layout = {
        "title": "Validação da Força Relativa (FR)",
        "xaxis": {
            "title": "Data",
            "type": "date",
        },
        "yaxis": {
            "title": "Preço Ajustado (Adj Close)",
            "tickformat": ".2f",
        },
        "hovermode": "closest",
        "legend": {
            "orientation": "h",
            "y": -0.3,
        },
    }

    return {
        "data": plotly_data,
        "layout": layout,
    }


# ===========================================================================
# Gráfico 2 — Candlestick (ativo selecionado na tabela)
# ===========================================================================


def build_candle_chart_payload(
    df_ticker: pd.DataFrame,
    ticker: str,
    start_idx: int = 20,
) -> Dict[str, Any]:
    """
    Monta o payload Plotly para o gráfico de candlestick de um ativo específico.

    Parâmetros
    ----------
    df_ticker : pd.DataFrame
        Slice do histórico referente ao ativo, com índice DatetimeIndex e colunas:
        Open, High, Low, Close, Volume, Adj Close, SMA_20, BB_UPPER_20,
        BB_LOWER_20, MACD_12_26, MACD_SIGNAL_9, MACD_HIST_12_26_9,
        STOP_ATR_14_1.5.
        Deve já conter a coluna "volume_medio" calculada externamente.
    ticker : str
        Símbolo do ativo (ex.: "PETR4").
    start_idx : int
        Quantidade de linhas iniciais a descartar para eliminar o período
        sem indicadores calculados. Default: 20.

    Retorno
    -------
    dict com as chaves:
    - "data"   : list[dict] — traces Plotly
    - "layout" : dict       — configuração do layout Plotly
    """

    if df_ticker is None or df_ticker.empty:
        raise ValueError(f"DataFrame vazio recebido para o ticker {ticker!r}")

    # ------------------------------------------------------------------
    # Prepara o slice final (ordenado, sem período sem indicadores)
    # ------------------------------------------------------------------
    df_plot = df_ticker.sort_index().iloc[start_idx:]

    # Eixo temporal e séries numéricas
    datas = df_plot.index.to_pydatetime().tolist()
    open_prices = df_plot["Open"].astype(float).tolist()
    high_prices = df_plot["High"].astype(float).tolist()
    low_prices = df_plot["Low"].astype(float).tolist()
    close_prices = df_plot["Close"].astype(float).tolist()
    volume = df_plot["Volume"].tolist()
    volume_medio = df_plot["volume_medio"].tolist()

    # Cores de volume: verde se fechamento > abertura, vermelho caso contrário
    volume_colors = [
        "green" if c > o else "red" for o, c in zip(open_prices, close_prices)
    ]

    # ------------------------------------------------------------------
    # Montagem das traces
    # ------------------------------------------------------------------
    plotly_data = []

    # Candlestick principal
    plotly_data.append(
        {
            "type": "candlestick",
            "x": datas,
            "open": open_prices,
            "high": high_prices,
            "low": low_prices,
            "close": close_prices,
            "name": ticker,
            "yaxis": "y",
        }
    )

    # Média Móvel Simples
    plotly_data.append(
        {
            "type": "scatter",
            "mode": "lines",
            "x": datas,
            "y": df_plot["SMA_20"].astype(float).tolist(),
            "name": "SMA 20",
            "line": {"color": "black"},
            "yaxis": "y",
        }
    )

    # Banda Superior de Bollinger
    plotly_data.append(
        {
            "type": "scatter",
            "mode": "lines",
            "x": datas,
            "y": df_plot["BB_UPPER_20"].astype(float).tolist(),
            "name": "Upper Band",
            "line": {"dash": "dash", "color": "gray"},
            "opacity": 0.5,
            "yaxis": "y",
        }
    )

    # Banda Inferior de Bollinger (com preenchimento até a banda superior)
    plotly_data.append(
        {
            "type": "scatter",
            "mode": "lines",
            "x": datas,
            "y": df_plot["BB_LOWER_20"].astype(float).tolist(),
            "name": "Lower Band",
            "line": {"dash": "dash", "color": "gray"},
            "fill": "tonexty",
            "opacity": 0.5,
            "yaxis": "y",
        }
    )

    # STOP ATR
    plotly_data.append(
        {
            "type": "scatter",
            "mode": "lines",
            "x": datas,
            "y": df_plot["STOP_ATR_14_1.5"].tolist(),
            "name": "STOP ATR",
            "line": {"shape": "hv", "color": "red"},
            "yaxis": "y",
        }
    )

    # Volume (barras)
    plotly_data.append(
        {
            "type": "bar",
            "x": datas,
            "y": volume,
            "marker": {"color": volume_colors},
            "name": "Volume",
            "yaxis": "y2",
            "showlegend": False,
        }
    )

    # Volume Médio (linha)
    plotly_data.append(
        {
            "type": "scatter",
            "mode": "lines",
            "x": datas,
            "y": volume_medio,
            "name": "Volume Médio",
            "line": {"color": "blue"},
            "yaxis": "y2",
        }
    )

    # MACD — linha principal
    plotly_data.append(
        {
            "type": "scatter",
            "mode": "lines",
            "x": datas,
            "y": df_plot["MACD_12_26"].tolist(),
            "name": "MACD",
            "line": {"color": "black"},
            "yaxis": "y3",
        }
    )

    # MACD — linha de sinal
    plotly_data.append(
        {
            "type": "scatter",
            "mode": "lines",
            "x": datas,
            "y": df_plot["MACD_SIGNAL_9"].tolist(),
            "name": "MACD Signal",
            "line": {"dash": "dash", "color": "gray"},
            "opacity": 0.5,
            "yaxis": "y3",
        }
    )

    # MACD — histograma
    plotly_data.append(
        {
            "type": "bar",
            "x": datas,
            "y": df_plot["MACD_HIST_12_26_9"].tolist(),
            "name": "MACD Hist",
            "marker": {"color": "gray"},
            "yaxis": "y3",
        }
    )

    # ------------------------------------------------------------------
    # Layout com subplots verticais
    # ------------------------------------------------------------------
    layout = {
        "height": 650,
        "title": f"Candlestick — {ticker}",
        "xaxis": {
            "title": "Data",
            "type": "date",
            "rangeslider": {"visible": False},
            "rangebreaks": [{"bounds": ["sat", "mon"]}],
        },
        "yaxis": {  # Candlestick + indicadores de preço
            "title": "Preço",
            "domain": [0.3, 1],
            "autorange": True,
            "rangemode": "normal",
        },
        "yaxis2": {  # Volume
            "title": "Volume",
            "domain": [0.15, 0.3],
            "showgrid": False,
        },
        "yaxis3": {  # MACD
            "title": "MACD",
            "domain": [0, 0.15],
            "showgrid": False,
        },
        "hovermode": "x unified",
    }

    return {
        "data": plotly_data,
        "layout": layout,
    }

```


## Assistant

---

### Etapa 4 — `routes.py` reescrito

Agora as routes orquestram apenas: *verificar cache → delegar → retornar*. Sem lógica de negócio inline.

**Tool Call: app\api\routes.py**
Status: Completed

Diff: C:\Users\Bruno\trend\app\api\routes.py
```
"""
routes.py

Camada de transporte HTTP da aplicação.

Responsabilidades:
- receber requisições HTTP e validar parâmetros de entrada
- orquestrar chamadas aos repositórios e builders (sem lógica de negócio inline)
- serializar e retornar respostas JSON

Este módulo NÃO:
- calcula indicadores técnicos
- executa scoring ou ranking
- monta payloads Plotly diretamente
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.charts.chart_builders import build_candle_chart_payload, build_fr_chart_payload
from app.core.init import init
from app.core.price_repository import price_repository
from app.core.ranking_pipeline import build_ranking_result
from app.core.ranking_repository import ranking_repository

router = APIRouter()


# ===========================================================================
# /api/fr-price-series
# Gráfico 1 — Força Relativa + tabela de ranking
# ===========================================================================


@router.get("/fr-price-series")
def get_fr_price_series(
    reference_date: Optional[str] = Query(
        default=str(date.today()),
        description="Data de referência no formato YYYY-MM-DD",
    ),
):
    """
    Endpoint principal acionado ao clicar em "Run".

    Garante que o histórico de preços e o resultado do ranking estejam
    calculados e cacheados. Retorna o payload completo para:
    - Gráfico 1 (Força Relativa) via Plotly
    - Tabela de ranking (embutida na resposta, sem chamada adicional ao backend)

    Retorno
    -------
    {
        "data"    : list[dict]  — traces Plotly para o gráfico de FR
        "layout"  : dict        — layout Plotly
        "ranking" : list[dict]  — ativos ranqueados prontos para a tabela
    }
    """

    # ------------------------------------------------------------------
    # 1. Garante histórico de preços com indicadores (passos 1–4)
    # ------------------------------------------------------------------
    if not price_repository.has(reference_date):
        prices = init(reference_date)
        price_repository.set(reference_date, prices)

    prices = price_repository.get(reference_date)

    # ------------------------------------------------------------------
    # 2. Garante resultado do pipeline de ranking (passos 5–9)
    #    build_ranking_result é executado uma única vez por reference_date
    # ------------------------------------------------------------------
    if not ranking_repository.has(reference_date):
        result = build_ranking_result(prices=prices, reference_date=reference_date)
        ranking_repository.set(reference_date, result)

    result = ranking_repository.get(reference_date)

    ranking = result.get("ranking", [])
    price_snapshots = result.get("price_snapshots")

    if not ranking:
        raise HTTPException(
            status_code=404,
            detail="Nenhum ativo passou pelo ranking para a data de referência informada.",
        )

    # ------------------------------------------------------------------
    # 3. Monta payload Plotly para o gráfico de FR
    # ------------------------------------------------------------------
    try:
        chart_payload = build_fr_chart_payload(
            price_snapshots=price_snapshots,
            ranking=ranking,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # ------------------------------------------------------------------
    # 4. Retorna gráfico + ranking em uma única resposta
    #    O frontend (fr_chart.js) usa result.ranking diretamente,
    #    eliminando a necessidade de chamar /api/ranking separadamente.
    # ------------------------------------------------------------------
    return {
        "data": chart_payload["data"],
        "layout": chart_payload["layout"],
        "ranking": ranking,
    }


# ===========================================================================
# /api/ranking
# Leitura do ranking cacheado (sem recomputação)
# ===========================================================================


@router.get("/ranking")
def get_ranking():
    """
    Retorna o ranking cacheado da última execução.

    Não reexecuta o pipeline — apenas lê o resultado já armazenado
    no RankingRepository pelo endpoint /api/fr-price-series.

    Útil como fallback ou para acesso direto ao ranking sem o gráfico.
    """

    try:
        reference_date = ranking_repository.current_reference_date()
        result = ranking_repository.get(reference_date)
    except (RuntimeError, KeyError) as exc:
        raise HTTPException(
            status_code=404,
            detail=(
                "Nenhum ranking disponível. "
                "Execute o pipeline via /api/fr-price-series primeiro."
            ),
        ) from exc

    return result["ranking"]


# ===========================================================================
# /api/candlechart
# Gráfico 2 — Candlestick do ativo selecionado na tabela
# ===========================================================================


@router.get("/candlechart")
def get_candlechart(
    ticker: str = Query(..., description="Ticker do ativo selecionado na tabela"),
):
    """
    Gera o payload Plotly para o gráfico de candlestick de um ativo específico.

    Usa o histórico completo já cacheado no PriceRepository (inclui todos
    os indicadores técnicos calculados no passo 4 do init).

    Parâmetros
    ----------
    ticker : str
        Símbolo do ativo (ex.: PETR4). Case-insensitive.

    Retorno
    -------
    {
        "data"   : list[dict] — traces Plotly (candlestick, SMA, BBands, MACD, volume)
        "layout" : dict       — layout Plotly com subplots verticais
    }
    """

    # ------------------------------------------------------------------
    # 1. Recupera histórico de preços do cache
    # ------------------------------------------------------------------
    try:
        reference_date = price_repository.current_reference_date()
        prices = price_repository.get(reference_date)
    except (RuntimeError, KeyError) as exc:
        raise HTTPException(
            status_code=404,
            detail=(
                "Histórico de preços não encontrado. "
                "Execute o pipeline via /api/fr-price-series primeiro."
            ),
        ) from exc

    ticker = ticker.strip().upper()

    # ------------------------------------------------------------------
    # 2. Extrai slice do ativo selecionado
    # ------------------------------------------------------------------
    try:
        df_ticker = prices.xs(ticker, level="Ticker", axis=1).copy()
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"Ticker {ticker!r} não encontrado no histórico carregado.",
        )

    if df_ticker.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Ticker {ticker!r} não possui dados no período carregado.",
        )

    # Indicador de volume médio calculado aqui pois é específico da visualização
    df_ticker["volume_medio"] = df_ticker["Volume"].rolling(window=20).mean()

    # ------------------------------------------------------------------
    # 3. Delega montagem do payload ao chart builder
    # ------------------------------------------------------------------
    try:
        chart_payload = build_candle_chart_payload(df_ticker=df_ticker, ticker=ticker)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return chart_payload

```


## Assistant

---

### Etapa 5 — `main.py`: remover endpoint `/run` órfão e o import de `run_pipeline`

**Tool Call: main.py**
Status: Completed

Diff: C:\Users\Bruno\trend\main.py
```
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.routes import router as api_router

# =========================================================
# FastAPI app
# =========================================================

app = FastAPI(
    title="Trend Following API",
    description="API para análise de força relativa e ranking de ativos da B3",
    version="0.1.0",
)

app.mount("/static", StaticFiles(directory="ui/static"), name="static")
templates = Jinja2Templates(directory="ui/templates")

# ------------------------------------------------------------------
# Registro dos routers
# ------------------------------------------------------------------
app.include_router(api_router, prefix="/api")


# =========================================================
# Endpoints de infraestrutura
# =========================================================


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
def health_check():
    """
    Endpoint simples para verificação de status da aplicação.
    """
    return {"status": "ok"}

```


## Assistant

---

Agora vamos verificar se há algum erro de importação residual no projeto inteiro:

**Tool Call: Check project diagnostics**
Status: Completed

C:\Users\Bruno\trend\app\services\ranking.py: 3 error(s), 0 warning(s)
C:\Users\Bruno\trend\app\data\preprocessing.py: 2 error(s), 2 warning(s)
C:\Users\Bruno\trend\app\data\preprocessing.py: 2 error(s), 0 warning(s)
C:\Users\Bruno\trend\app\api\routes.py: 7 error(s), 0 warning(s)
C:\Users\Bruno\trend\app\core\ranking_pipeline.py: 3 error(s), 0 warning(s)
C:\Users\Bruno\trend\app\core\init.py: 0 error(s), 15 warning(s)
C:\Users\Bruno\trend\app\core\init.py: 2 error(s), 0 warning(s)


**Tool Call: Check diagnostics for `C:\Users\Bruno\trend\app\api\routes.py`**
Status: Completed

error at line 64: Argument of type "str | None" cannot be assigned to parameter "reference_date" of type "str" in function "has"
  Type "str | None" is not assignable to type "str"
    "None" is not assignable to "str"
error at line 66: Argument of type "str | None" cannot be assigned to parameter "reference_date" of type "str" in function "set"
  Type "str | None" is not assignable to type "str"
    "None" is not assignable to "str"
error at line 68: Argument of type "str | None" cannot be assigned to parameter "reference_date" of type "str" in function "get"
  Type "str | None" is not assignable to type "str"
    "None" is not assignable to "str"
error at line 74: Argument of type "str | None" cannot be assigned to parameter "reference_date" of type "str" in function "has"
  Type "str | None" is not assignable to type "str"
    "None" is not assignable to "str"
error at line 76: Argument of type "str | None" cannot be assigned to parameter "reference_date" of type "str" in function "set"
  Type "str | None" is not assignable to type "str"
    "None" is not assignable to "str"
error at line 78: Argument of type "str | None" cannot be assigned to parameter "reference_date" of type "str" in function "get"
  Type "str | None" is not assignable to type "str"
    "None" is not assignable to "str"
error at line 94: Argument of type "Any | None" cannot be assigned to parameter "price_snapshots" of type "DataFrame" in function "build_fr_chart_payload"
  Type "Any | None" is not assignable to type "DataFrame"
    "None" is not assignable to "DataFrame"


**Tool Call: Check diagnostics for `C:\Users\Bruno\trend\app\core\ranking_pipeline.py`**
Status: Completed

error at line 85: Argument of type "str | None" cannot be assigned to parameter "reference_date" of type "str | Timestamp" in function "generate_theoretical_dates"
  Type "str | None" is not assignable to type "str | Timestamp"
    Type "None" is not assignable to type "str | Timestamp"
      "None" is not assignable to "str"
      "None" is not assignable to "Timestamp"
error at line 88: Argument of type "Index" cannot be assigned to parameter "index" of type "DatetimeIndex" in function "resolve_to_trading_dates"
  "Index" is not assignable to "DatetimeIndex"
error at line 167: "__getitem__" method not defined on type "numpy.bool[builtins.bool]"


**Tool Call: Check diagnostics for `C:\Users\Bruno\trend\app\core\init.py`**
Status: Completed

warning at line 10: `typing.Dict` imported but unused
warning at line 10: `typing.Any` imported but unused
warning at line 15: `app.data.market_data.get_asset_metadata` imported but unused
warning at line 15: `app.data.market_data.get_price_history` imported but unused
warning at line 19: `app.data.market_data.enrich_with_metadata_and_52w_high` imported but unused
warning at line 23: `app.data.preprocessing.resolve_to_trading_dates` imported but unused
warning at line 24: `app.data.preprocessing.extract_price_snapshots` imported but unused
warning at line 25: `app.data.preprocessing.flatten_snapshot_for_scoring` imported but unused
warning at line 26: `app.data.preprocessing.build_price_matrix_for_chart` imported but unused
warning at line 27: `app.data.preprocessing.build_plotly_price_dataframe` imported but unused
warning at line 28: `app.data.preprocessing.add_percent_change_for_hover` imported but unused
warning at line 29: `app.data.preprocessing.extract_latest` imported but unused
warning at line 32: `app.services.scoring.calculate_relative_strength` imported but unused
warning at line 33: `app.services.ranking.build_ranking` imported but unused
warning at line 40: `app.finance.indicators.calculate_risk_return_indicators` imported but unused
error at line 88: Argument of type "Timestamp" cannot be assigned to parameter "start" of type "str" in function "download_price_history"
  "Timestamp" is not assignable to "str"
error at line 89: Argument of type "Timestamp" cannot be assigned to parameter "end" of type "str" in function "download_price_history"
  "Timestamp" is not assignable to "str"


## Assistant

<thinking>
Let me analyze the diagnostics:

1. **routes.py**: `reference_date` is `Optional[str]` which is `str | None`, but repositories expect `str`. Need to resolve `None` to today's date before passing to repositories. Also `price_snapshots` could be `None`.

2. **ranking_pipeline.py**: 
   - `generate_theoretical_dates` doesn't accept `None`, need to resolve first
   - `resolve_to_trading_dates` expects `DatetimeIndex`, not `Index`
   - Line 167 numpy bool indexing issue (pre-existing)
   
3. **init.py** has pre-existing warnings and errors I didn't introduce, so I'll focus on my changes.

For the fixes, I need to resolve `reference_date` from `Optional[str]` to `str` at the start of the routes endpoint and handle the `price_snapshots` None case, then do the same resolution in ranking_pipeline before calling `generate_theoretical_dates` and fix the `Index` vs `DatetimeIndex` type mismatch.

The numpy bool issue and the type annotation problem with `resolve_to_trading_dates` are pre-existing, so I'll leave those alone.
</thinking>

Os erros são de dois tipos: os que eu introduzi (anotações de tipo com `str | None`) e os que já existiam antes. Vou corrigir os meus:

**Tool Call: app\api\routes.py**
Status: Completed

Diff: C:\Users\Bruno\trend\app\api\routes.py
```
"""
routes.py

Camada de transporte HTTP da aplicação.

Responsabilidades:
- receber requisições HTTP e validar parâmetros de entrada
- orquestrar chamadas aos repositórios e builders (sem lógica de negócio inline)
- serializar e retornar respostas JSON

Este módulo NÃO:
- calcula indicadores técnicos
- executa scoring ou ranking
- monta payloads Plotly diretamente
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.charts.chart_builders import build_candle_chart_payload, build_fr_chart_payload
from app.core.init import init
from app.core.price_repository import price_repository
from app.core.ranking_pipeline import build_ranking_result
from app.core.ranking_repository import ranking_repository

router = APIRouter()


# ===========================================================================
# /api/fr-price-series
# Gráfico 1 — Força Relativa + tabela de ranking
# ===========================================================================


@router.get("/fr-price-series")
def get_fr_price_series(
    reference_date: Optional[str] = Query(
        default=None,
        description="Data de referência no formato YYYY-MM-DD",
    ),
):
    """
    Endpoint principal acionado ao clicar em "Run".

    Garante que o histórico de preços e o resultado do ranking estejam
    calculados e cacheados. Retorna o payload completo para:
    - Gráfico 1 (Força Relativa) via Plotly
    - Tabela de ranking (embutida na resposta, sem chamada adicional ao backend)

    Retorno
    -------
    {
        "data"    : list[dict]  — traces Plotly para o gráfico de FR
        "layout"  : dict        — layout Plotly
        "ranking" : list[dict]  — ativos ranqueados prontos para a tabela
    }
    """

    # Garante que reference_date seja sempre uma str concreta
    reference_date = reference_date or str(date.today())

    # ------------------------------------------------------------------
    # 1. Garante histórico de preços com indicadores (passos 1–4)
    # ------------------------------------------------------------------
    if not price_repository.has(reference_date):
        prices = init(reference_date)
        price_repository.set(reference_date, prices)

    prices = price_repository.get(reference_date)

    # ------------------------------------------------------------------
    # 2. Garante resultado do pipeline de ranking (passos 5–9)
    #    build_ranking_result é executado uma única vez por reference_date
    # ------------------------------------------------------------------
    if not ranking_repository.has(reference_date):
        result = build_ranking_result(prices=prices, reference_date=reference_date)
        ranking_repository.set(reference_date, result)

    result = ranking_repository.get(reference_date)

    ranking = result.get("ranking", [])
    price_snapshots: pd.DataFrame = result["price_snapshots"]

    if not ranking:
        raise HTTPException(
            status_code=404,
            detail="Nenhum ativo passou pelo ranking para a data de referência informada.",
        )

    # ------------------------------------------------------------------
    # 3. Monta payload Plotly para o gráfico de FR
    # ------------------------------------------------------------------
    try:
        chart_payload = build_fr_chart_payload(
            price_snapshots=price_snapshots,
            ranking=ranking,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # ------------------------------------------------------------------
    # 4. Retorna gráfico + ranking em uma única resposta
    #    O frontend (fr_chart.js) usa result.ranking diretamente,
    #    eliminando a necessidade de chamar /api/ranking separadamente.
    # ------------------------------------------------------------------
    return {
        "data": chart_payload["data"],
        "layout": chart_payload["layout"],
        "ranking": ranking,
    }


# ===========================================================================
# /api/ranking
# Leitura do ranking cacheado (sem recomputação)
# ===========================================================================


@router.get("/ranking")
def get_ranking():
    """
    Retorna o ranking cacheado da última execução.

    Não reexecuta o pipeline — apenas lê o resultado já armazenado
    no RankingRepository pelo endpoint /api/fr-price-series.

    Útil como fallback ou para acesso direto ao ranking sem o gráfico.
    """

    try:
        reference_date = ranking_repository.current_reference_date()
        result = ranking_repository.get(reference_date)
    except (RuntimeError, KeyError) as exc:
        raise HTTPException(
            status_code=404,
            detail=(
                "Nenhum ranking disponível. "
                "Execute o pipeline via /api/fr-price-series primeiro."
            ),
        ) from exc

    return result["ranking"]


# ===========================================================================
# /api/candlechart
# Gráfico 2 — Candlestick do ativo selecionado na tabela
# ===========================================================================


@router.get("/candlechart")
def get_candlechart(
    ticker: str = Query(..., description="Ticker do ativo selecionado na tabela"),
):
    """
    Gera o payload Plotly para o gráfico de candlestick de um ativo específico.

    Usa o histórico completo já cacheado no PriceRepository (inclui todos
    os indicadores técnicos calculados no passo 4 do init).

    Parâmetros
    ----------
    ticker : str
        Símbolo do ativo (ex.: PETR4). Case-insensitive.

    Retorno
    -------
    {
        "data"   : list[dict] — traces Plotly (candlestick, SMA, BBands, MACD, volume)
        "layout" : dict       — layout Plotly com subplots verticais
    }
    """

    # ------------------------------------------------------------------
    # 1. Recupera histórico de preços do cache
    # ------------------------------------------------------------------
    try:
        reference_date = price_repository.current_reference_date()
        prices = price_repository.get(reference_date)
    except (RuntimeError, KeyError) as exc:
        raise HTTPException(
            status_code=404,
            detail=(
                "Histórico de preços não encontrado. "
                "Execute o pipeline via /api/fr-price-series primeiro."
            ),
        ) from exc

    ticker = ticker.strip().upper()

    # ------------------------------------------------------------------
    # 2. Extrai slice do ativo selecionado
    # ------------------------------------------------------------------
    try:
        df_ticker = prices.xs(ticker, level="Ticker", axis=1).copy()
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"Ticker {ticker!r} não encontrado no histórico carregado.",
        )

    if df_ticker.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Ticker {ticker!r} não possui dados no período carregado.",
        )

    # Indicador de volume médio calculado aqui pois é específico da visualização
    df_ticker["volume_medio"] = df_ticker["Volume"].rolling(window=20).mean()

    # ------------------------------------------------------------------
    # 3. Delega montagem do payload ao chart builder
    # ------------------------------------------------------------------
    try:
        chart_payload = build_candle_chart_payload(df_ticker=df_ticker, ticker=ticker)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return chart_payload

```


**Tool Call: app\core\ranking_pipeline.py**
Status: Completed

Diff: C:\Users\Bruno\trend\app\core\ranking_pipeline.py
```
"""
ranking_pipeline.py

Pipeline de scoring, ranking e enriquecimento de ativos (passos 5–9).

Responsabilidades:
- resolver datas de pregão válidas a partir de datas teóricas
- extrair snapshots de preço por data
- calcular Força Relativa (scoring)
- ranquear e filtrar ativos
- enriquecer o ranking com metadados, indicadores e métricas de risco/retorno
- sanitizar e estruturar o payload final

Este módulo NÃO:
- baixa dados de mercado
- calcula indicadores técnicos no histórico completo
- monta payloads Plotly
- conhece endpoints ou detalhes de HTTP
"""

from typing import Any, Dict

import numpy as np
import pandas as pd

import app.config as config
from app.data.market_data import (
    enrich_with_metadata_and_52w_high,
    generate_theoretical_dates,
)
from app.data.preprocessing import (
    extract_latest,
    extract_price_snapshots,
    flatten_snapshot_for_scoring,
    resolve_to_trading_dates,
)
from app.finance.indicators import calculate_risk_return_indicators
from app.services.ranking import build_ranking
from app.services.scoring import calculate_relative_strength


def build_ranking_result(
    prices: pd.DataFrame,
    reference_date: str | None = None,
) -> Dict[str, Any]:
    """
    Executa os passos 5–9 do pipeline: scoring → ranking → enriquecimento.

    Assume que ``prices`` já foi:
    - baixado e normalizado (passo 1–3, responsabilidade de ``init``)
    - enriquecido com indicadores técnicos no histórico completo (passo 4)

    Parâmetros
    ----------
    prices : pd.DataFrame
        DataFrame MultiIndex (Field, Ticker) com histórico de preços e
        indicadores técnicos já calculados.
    reference_date : str | None
        Data de referência no formato YYYY-MM-DD.
        Se None, usa a data de hoje.

    Retorno
    -------
    dict com as chaves:
    - ``"summary"``         : dict com métricas resumidas da execução
    - ``"ranking"``         : list[dict] dos ativos ranqueados e enriquecidos,
                              prontos para serialização JSON
    - ``"price_snapshots"`` : pd.DataFrame MultiIndex com snapshots de preço
                              nas datas resolvidas (consumido pelo chart builder)

    Retornos antecipados (sem erro):
    - Nenhum ativo pontuado  → ranking e price_snapshots vazios
    - Nenhum ativo no ranking → ranking vazio, price_snapshots disponível
    """

    # ------------------------------------------------------------------
    # 5. Extração do último valor de indicadores por ticker
    # ------------------------------------------------------------------
    df_latest = extract_latest(prices, price_field="Adj Close", indicator_fields=None)
    df_latest["Ticker"] = df_latest["Ticker"].astype(str).str.strip().str.upper()

    # ------------------------------------------------------------------
    # 6. Resolução das datas válidas e extração de snapshots
    # ------------------------------------------------------------------
    # Garante que reference_date seja sempre uma str concreta antes de
    # repassar para generate_theoretical_dates, que não aceita None
    reference_date = reference_date or str(pd.Timestamp.today().date())

    theoretical_dates = generate_theoretical_dates(reference_date)

    trading_dates = resolve_to_trading_dates(
        prices.index,
        theoretical_dates,
    )

    price_snapshots = extract_price_snapshots(
        prices,
        trading_dates,
        price_field="Adj Close",
    )

    # flat: índice = ticker, colunas = p0..pN (preços nas datas selecionadas)
    df_flat = flatten_snapshot_for_scoring(price_snapshots)

    # ------------------------------------------------------------------
    # 7. Scoring — Força Relativa (FR)
    # ------------------------------------------------------------------
    scored = calculate_relative_strength(df_flat)

    if scored.empty:
        return {
            "summary": {"message": "Nenhum ativo pontuado"},
            "ranking": [],
            "price_snapshots": price_snapshots,
        }

    # ------------------------------------------------------------------
    # 8. Ranking — ordenação, percentil e filtro
    # ------------------------------------------------------------------
    ranking_result = build_ranking(
        df=scored,
        score_column="FR",
        min_score=config.MIN_FR,
        top_n=config.TOP_N,
        payload_fields=["FR", "FR_rank"],
    )

    if not ranking_result["payload"]:
        return {
            "summary": {"message": "Nenhum ativo passou no ranking"},
            "ranking": [],
            "price_snapshots": price_snapshots,
        }

    # ------------------------------------------------------------------
    # 9. Pós-ranking: merge com últimos valores + metadados + risco/retorno
    # ------------------------------------------------------------------
    df_ranked = pd.DataFrame(ranking_result["payload"])
    df_ranked["ticker"] = df_ranked["ticker"].astype(str).str.strip().str.upper()

    df_latest = df_latest.rename(columns={"Ticker": "ticker"})

    df_ranked = df_ranked.merge(
        df_latest,
        on="ticker",
        how="left",
        validate="m:1",
    )

    df_enriched = enrich_with_metadata_and_52w_high(
        df=df_ranked,
        ticker_column="ticker",
    )

    df_final = calculate_risk_return_indicators(
        df=df_enriched,
        price_col="Adj Close",
        stop_col="STOP_ATR_14_1.5",
        high_52w_col="high_52w",
    )

    # ------------------------------------------------------------------
    # 10. Sanitização para serialização JSON
    # ------------------------------------------------------------------
    df_clean = df_final.copy()
    df_clean.replace([np.inf, -np.inf], np.nan, inplace=True)

    num_cols = df_clean.select_dtypes(include=[np.number])
    non_finite_mask = ~np.isfinite(num_cols)
    if non_finite_mask.any().any():
        bad_cols = non_finite_mask.any()[non_finite_mask.any()].index.tolist()
        print(f"[ranking_pipeline] Colunas com valores não finitos: {bad_cols}")

    ranking_records = df_clean.to_dict(orient="records")

    # Substitui float não-finitos por None (JSON-safe)
    for row in ranking_records:
        for key, value in row.items():
            if isinstance(value, float) and not np.isfinite(value):
                row[key] = None

    # ------------------------------------------------------------------
    # 11. Montagem do retorno
    # ------------------------------------------------------------------
    summary = {
        "scored_assets": len(scored),
        "ranked_assets": len(ranking_records),
        "reference_date": reference_date,
    }

    return {
        "summary": summary,
        "ranking": ranking_records,
        "price_snapshots": price_snapshots,
    }

```


**Tool Call: Check diagnostics for `C:\Users\Bruno\trend\app\api\routes.py`**
Status: Completed

error at line 84: "pd" is not defined
error at line 84: Undefined name `pd`


**Tool Call: Check diagnostics for `C:\Users\Bruno\trend\app\core\ranking_pipeline.py`**
Status: Completed

error at line 92: Argument of type "Index" cannot be assigned to parameter "index" of type "DatetimeIndex" in function "resolve_to_trading_dates"
  "Index" is not assignable to "DatetimeIndex"
error at line 171: "__getitem__" method not defined on type "numpy.bool[builtins.bool]"


**Tool Call: app\api\routes.py**
Status: Completed

Diff: C:\Users\Bruno\trend\app\api\routes.py
```
"""
routes.py

Camada de transporte HTTP da aplicação.

Responsabilidades:
- receber requisições HTTP e validar parâmetros de entrada
- orquestrar chamadas aos repositórios e builders (sem lógica de negócio inline)
- serializar e retornar respostas JSON

Este módulo NÃO:
- calcula indicadores técnicos
- executa scoring ou ranking
- monta payloads Plotly diretamente
"""

from datetime import date
from typing import Optional

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from app.charts.chart_builders import build_candle_chart_payload, build_fr_chart_payload
from app.core.init import init
from app.core.price_repository import price_repository
from app.core.ranking_pipeline import build_ranking_result
from app.core.ranking_repository import ranking_repository

router = APIRouter()


# ===========================================================================
# /api/fr-price-series
# Gráfico 1 — Força Relativa + tabela de ranking
# ===========================================================================


@router.get("/fr-price-series")
def get_fr_price_series(
    reference_date: Optional[str] = Query(
        default=None,
        description="Data de referência no formato YYYY-MM-DD",
    ),
):
    """
    Endpoint principal acionado ao clicar em "Run".

    Garante que o histórico de preços e o resultado do ranking estejam
    calculados e cacheados. Retorna o payload completo para:
    - Gráfico 1 (Força Relativa) via Plotly
    - Tabela de ranking (embutida na resposta, sem chamada adicional ao backend)

    Retorno
    -------
    {
        "data"    : list[dict]  — traces Plotly para o gráfico de FR
        "layout"  : dict        — layout Plotly
        "ranking" : list[dict]  — ativos ranqueados prontos para a tabela
    }
    """

    # Garante que reference_date seja sempre uma str concreta
    reference_date = reference_date or str(date.today())

    # ------------------------------------------------------------------
    # 1. Garante histórico de preços com indicadores (passos 1–4)
    # ------------------------------------------------------------------
    if not price_repository.has(reference_date):
        prices = init(reference_date)
        price_repository.set(reference_date, prices)

    prices = price_repository.get(reference_date)

    # ------------------------------------------------------------------
    # 2. Garante resultado do pipeline de ranking (passos 5–9)
    #    build_ranking_result é executado uma única vez por reference_date
    # ------------------------------------------------------------------
    if not ranking_repository.has(reference_date):
        result = build_ranking_result(prices=prices, reference_date=reference_date)
        ranking_repository.set(reference_date, result)

    result = ranking_repository.get(reference_date)

    ranking = result.get("ranking", [])
    price_snapshots: pd.DataFrame = result["price_snapshots"]

    if not ranking:
        raise HTTPException(
            status_code=404,
            detail="Nenhum ativo passou pelo ranking para a data de referência informada.",
        )

    # ------------------------------------------------------------------
    # 3. Monta payload Plotly para o gráfico de FR
    # ------------------------------------------------------------------
    try:
        chart_payload = build_fr_chart_payload(
            price_snapshots=price_snapshots,
            ranking=ranking,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # ------------------------------------------------------------------
    # 4. Retorna gráfico + ranking em uma única resposta
    #    O frontend (fr_chart.js) usa result.ranking diretamente,
    #    eliminando a necessidade de chamar /api/ranking separadamente.
    # ------------------------------------------------------------------
    return {
        "data": chart_payload["data"],
        "layout": chart_payload["layout"],
        "ranking": ranking,
    }


# ===========================================================================
# /api/ranking
# Leitura do ranking cacheado (sem recomputação)
# ===========================================================================


@router.get("/ranking")
def get_ranking():
    """
    Retorna o ranking cacheado da última execução.

    Não reexecuta o pipeline — apenas lê o resultado já armazenado
    no RankingRepository pelo endpoint /api/fr-price-series.

    Útil como fallback ou para acesso direto ao ranking sem o gráfico.
    """

    try:
        reference_date = ranking_repository.current_reference_date()
        result = ranking_repository.get(reference_date)
    except (RuntimeError, KeyError) as exc:
        raise HTTPException(
            status_code=404,
            detail=(
                "Nenhum ranking disponível. "
                "Execute o pipeline via /api/fr-price-series primeiro."
            ),
        ) from exc

    return result["ranking"]


# ===========================================================================
# /api/candlechart
# Gráfico 2 — Candlestick do ativo selecionado na tabela
# ===========================================================================


@router.get("/candlechart")
def get_candlechart(
    ticker: str = Query(..., description="Ticker do ativo selecionado na tabela"),
):
    """
    Gera o payload Plotly para o gráfico de candlestick de um ativo específico.

    Usa o histórico completo já cacheado no PriceRepository (inclui todos
    os indicadores técnicos calculados no passo 4 do init).

    Parâmetros
    ----------
    ticker : str
        Símbolo do ativo (ex.: PETR4). Case-insensitive.

    Retorno
    -------
    {
        "data"   : list[dict] — traces Plotly (candlestick, SMA, BBands, MACD, volume)
        "layout" : dict       — layout Plotly com subplots verticais
    }
    """

    # ------------------------------------------------------------------
    # 1. Recupera histórico de preços do cache
    # ------------------------------------------------------------------
    try:
        reference_date = price_repository.current_reference_date()
        prices = price_repository.get(reference_date)
    except (RuntimeError, KeyError) as exc:
        raise HTTPException(
            status_code=404,
            detail=(
                "Histórico de preços não encontrado. "
                "Execute o pipeline via /api/fr-price-series primeiro."
            ),
        ) from exc

    ticker = ticker.strip().upper()

    # ------------------------------------------------------------------
    # 2. Extrai slice do ativo selecionado
    # ------------------------------------------------------------------
    try:
        df_ticker = prices.xs(ticker, level="Ticker", axis=1).copy()
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"Ticker {ticker!r} não encontrado no histórico carregado.",
        )

    if df_ticker.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Ticker {ticker!r} não possui dados no período carregado.",
        )

    # Indicador de volume médio calculado aqui pois é específico da visualização
    df_ticker["volume_medio"] = df_ticker["Volume"].rolling(window=20).mean()

    # ------------------------------------------------------------------
    # 3. Delega montagem do payload ao chart builder
    # ------------------------------------------------------------------
    try:
        chart_payload = build_candle_chart_payload(df_ticker=df_ticker, ticker=ticker)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return chart_payload

```


**Tool Call: Check diagnostics for `C:\Users\Bruno\trend\app\api\routes.py`**
Status: Completed

File doesn't have errors or warnings!

## Assistant

Sem erros em `routes.py`. Os dois erros restantes em `ranking_pipeline.py` são pré-existentes — `resolve_to_trading_dates` e a indexação numpy já estavam assim antes da refatoração. Confirmo:

**Tool Call: Search files for regex `def resolve_to_trading_dates`**
Status: Completed

Found 1 matches:

## Matches in trend\app\data\preprocessing.py

### def resolve_to_trading_dates › L4-14
```
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
```

8 lines remaining in ancestor node. Read the file to see all.


## Assistant

<thinking>
The type annotation says `pd.DatetimeIndex` but `prices.index` returns `pd.Index` generically. This is a pre-existing issue with the type annotation - the function works correctly at runtime because `prices.index` is actually a `DatetimeIndex`, but the type checker can't infer it. This isn't something I introduced, and it's not breaking. The numpy bool issue in line 171 is also pre-existing.

Let me give the user a summary of the final state.
</thinking>

A anotação `pd.DatetimeIndex` em `resolve_to_trading_dates` é pré-existente — a função recebe `prices.index` que em runtime já é um `DatetimeIndex`, mas o type checker infere como `Index` genérico. Não é quebra funcional e não foi introduzido pela refatoração.

---

## Resumo do que foi feito

### Arquivos criados
| Arquivo | Conteúdo |
|---|---|
| `app/core/ranking_repository.py` | Cache do resultado do pipeline de ranking, espelhando o `PriceRepository` |
| `app/core/ranking_pipeline.py` | Pipeline de scoring/ranking/enriquecimento com a função `build_ranking_result` |
| `app/charts/chart_builders.py` | Toda a lógica de montagem Plotly: `build_fr_chart_payload` e `build_candle_chart_payload` |

### Arquivos modificados
| Arquivo | O que mudou |
|---|---|
| `app/api/routes.py` | `/fr-price-series` usa cache duplo e retorna `ranking` embutido; `/ranking` virou leitura pura do cache; `/candlechart` delega ao `chart_builder` |
| `main.py` | Removido endpoint `/run` órfão e import de `run_pipeline` |

### Arquivos removidos
| Arquivo | Motivo |
|---|---|
| `app/core/pipeline.py` | Substituído integralmente por `ranking_pipeline.py` |

### O que resolve o problema central

O fluxo agora é assim:

```/dev/null/flow.txt#L1-12
Run clicado
    └── /api/fr-price-series
            ├── price_repository.has?  NÃO → init() → price_repository.set()
            ├── ranking_repository.has? NÃO → build_ranking_result() → ranking_repository.set()
            │                           SIM → lê do cache (zero recomputação)
            ├── build_fr_chart_payload()
            └── retorna { data, layout, ranking }
                    │
                    ├── Plotly renderiza gráfico 1
                    └── fr_chart.js usa result.ranking diretamente
                            → renderRankingTable(result.ranking)
                            → /api/ranking NÃO é mais chamado no fluxo normal
```

`build_ranking_result` executa **uma única vez** por `reference_date`. `/api/ranking` existe como fallback leve — só lê do `RankingRepository`, sem tocar em nenhum cálculo.

## User

Segue abaixo uma função da versão antiga do projeto, para executar um gráfico de dispersão com dados já calculados. Identifique a possível fonte de dados para criar o gráfico, e construa as funções e os endpoints necessários para exibir esse gráfico abaixo do gráfico gerado por candlechart.js

```
fig = px.scatter(
        df,
        x='distancia',
        y='Risco_%',        
        color='sector',        
        text='Acao',
        hover_data=['Retorno_Risco'],
        labels={},
        title='Grafico de bolhas, por setor'
    )

    #adicionando as linhas que irão dividir os quadrantes:
    #linha vertical no meio do intervalo do eixo X (distancia)    
    # Ponto médio para a linha vertical
    mid_x = df['distancia'].max() / 2
    mid_y = df['Risco_%'].max() / 2

    # Desenhando a linha vertical
    fig.add_trace(go.Scatter(
        x=[mid_x, mid_x],
        y=[df['Risco_%'].min() - 1, df['Risco_%'].max() + 1],
        mode='lines',
        line=dict(color='red', dash='dash'),
        showlegend=False
        ))

    #linha horizontal
    # Ponto médio para a linha horizontal    
    #mid_yy = df['Risco_%'].median()

    # Desenhando a linha horizontal
    fig.add_trace(go.Scatter(
        x=[df['distancia'].min() - 1, df['distancia'].max() + 1],
        y=[mid_y, mid_y],
        mode='lines',
        line=dict(color='red', dash='dash'),
        showlegend=False
        ))

    fig.update_traces(textposition="bottom right")
    ```

## Assistant

<thinking>
Let me analyze the scatter plot function to understand what data it needs:

1. `distancia` - distance (likely price distance from some reference, like 52w high or moving average)
2. `Risco_%` - Risk percentage (likely ATR-based stop loss as % of price)
3. `sector` - sector of the stock
4. `Acao` - stock ticker/name
5. `Retorno_Risco` - Risk/Return ratio

Now let me look at what's already calculated in the ranking result to see which fields are available. Let me check the existing files to understand what's already computed.

From what I've seen:
- `enrich_with_metadata_and_52w_high` - adds metadata and 52-week high


- `calculate_risk_return_indicators` - calculates risk/return indicators
- The ranking payload already has all enriched data

Let me examine those files to see what columns are available.
</thinking>

Antes de escrever qualquer código, deixa eu mapear com precisão quais campos já existem no projeto.

**Tool Call: Read file `app\finance\indicators.py`**
Status: Completed

```json
{
  "Text": "import pandas as pd\nimport numpy as np\n\n\ndef calculate_risk_return_indicators(\n    df: pd.DataFrame,\n    price_col: str = \"Adj Close\",\n    stop_col: str = \"STOP_ATR_14_1.5\",\n    high_52w_col: str = \"high_52w\",\n    round_decimals: int = 2,\n) -> pd.DataFrame:\n    \"\"\"\n    Calcula indicadores customizados de risco e retorno.\n\n    Indicadores calculados:\n    - distancia: diferença percentual entre o preço máximo das últimas\n      52 semanas e o preço atual.\n    - Risco_%: perda percentual assumida caso o ativo atinja o stop ATR.\n    - Retorno_Risco: relação entre retorno potencial e risco assumido.\n\n    Parâmetros\n    ----------\n    df\n        DataFrame enriquecido contendo preços, stop_atr e high_52w.\n    price_col\n        Coluna com o preço atual (preferencialmente Adj Close).\n    stop_col\n        Coluna com o valor do stop baseado em ATR.\n    high_52w_col\n        Coluna com o preço máximo das últimas 52 semanas.\n    round_decimals\n        Número de casas decimais para arredondamento final.\n\n    Retorna\n    -------\n    pd.DataFrame\n        DataFrame com as novas colunas:\n        - distancia\n        - Risco_%\n        - Retorno_Risco\n    \"\"\"\n\n    df = df.copy()\n\n    # ------------------------------------------------------------------\n    # Distância até o topo de 52 semanas (%)\n    # ------------------------------------------------------------------\n    df[\"distancia\"] = np.where(\n        df[high_52w_col] > 0,\n        ((df[high_52w_col] - df[price_col]) / df[high_52w_col]) * 100,\n        np.nan,\n    )\n\n    # ------------------------------------------------------------------\n    # Risco percentual até o stop ATR\n    # ------------------------------------------------------------------\n    df[\"Risco_%\"] = np.where(\n        df[stop_col] > 0,\n        ((df[price_col] - df[stop_col]) / df[stop_col]) * 100,\n        np.nan,\n    )\n\n    # ------------------------------------------------------------------\n    # Relação Retorno / Risco\n    # ------------------------------------------------------------------\n    df[\"Retorno_Risco\"] = np.where(\n        df[\"Risco_%\"] != 0,\n        df[\"distancia\"] / df[\"Risco_%\"],\n        np.nan,\n    )\n\n    # ------------------------------------------------------------------\n    # Arredondamento final (apenas métricas derivadas)\n    # ------------------------------------------------------------------\n    cols_to_round = [\"distancia\", \"Risco_%\", \"Retorno_Risco\"]\n    df[cols_to_round] = df[cols_to_round].round(round_decimals)\n\n    return df\n"
}
```

**Tool Call: Read file `app\data\market_data.py`**
Status: Completed

```json
{
  "Text": "\"\"\"\nmarket_data.py\n\nCamada responsável exclusivamente pela obtenção e padronização\nde dados de mercado.\n\nFontes:\n- BRAPI: listagem completa de ativos da B3\n- yfinance: preços históricos e metadados dos ativos\n\nEste módulo NÃO aplica indicadores técnicos, filtros de estratégia\nou regras de decisão.\n\"\"\"\n\nfrom __future__ import annotations\n\nimport requests\nimport pandas as pd\nimport yfinance as yf\nfrom typing import Iterable, List, Optional, Literal\n\nfrom datetime import datetime\nfrom dateutil.relativedelta import relativedelta\nfrom brapi import Brapi\n\n\n\nBRAPI_BASE_URL = \"https://brapi.dev/api\"\nBRAPI_STOCK_LIST_ENDPOINT = \"/quote/list\"\nBRAPI_TOKEN = \"ikKPyJs6dZwA3GUp2SX46z\"\n\n\ndef list_b3_assets(min_price: float = 4.0,\n                   min_volume: float = 1_000_000,\n                   excluded_suffixes: Iterable[str] = (\"11\", \"32\"),\n                   add_yfinance_suffix: bool = True,\n                   timeout: int = 30) -> List[str]:\n    \"\"\"\n    Obtém a lista completa de ativos da B3 via BRAPI e aplica filtros básicos.\n\n    Parâmetros\n    ----------\n    min_price : float, default=5.0\n        Preço mínimo do ativo.\n\n    min_volume : float, default=1_000_000\n        Volume financeiro mínimo.\n\n    excluded_suffixes : Iterable[str], default=(\"11\", \"32\")\n        Sufixos de tickers a serem excluídos.\n\n    add_yfinance_suffix : bool, default=True\n        Adiciona o sufixo '.SA' aos tickers para compatibilidade com yfinance.\n\n    timeout : int, default=30\n        Timeout da requisição HTTP.\n\n    Retorno\n    -------\n    list[str]\n        Lista de tickers filtrados e padronizados.\n    \"\"\"\n    client = Brapi(\n        api_key=BRAPI_TOKEN, \n        environment=\"production\",\n    )\n    stocks = client.quote.list()\n    #change, stock, sector, name, close, logo, type, market_cap, volume\n    data=[]\n    for stock in stocks.stocks: #para cada ativo, retornar nome/ticket, close, volume\n        data.append({\n            \"ticket\": stock.stock,\n            \"name\": stock.name,\n            \"close\": stock.close,\n            \"sector\": stock.sector,\n            \"volume\": stock.volume\n        })\n\n    df = pd.DataFrame.from_dict(data) #cria dataframe a partir do dict data\n    print(df.head())\n    dff = df[ (df['volume'] > min_volume) &  (df['close'] > min_price) ]\n    dff = dff[['ticket', 'name', 'close', 'sector', 'volume']].sort_values(by='ticket')\n    substring = ['11', '32']\n    dff_negative = dff['ticket'].str.contains('|'.join(substring))\n    dff = dff[~dff_negative]\n    \n    sfx = '.SA' #incluir o sufixo .SA\n    acoess = dff['ticket'].apply(lambda x: f\"{x}{sfx}\").values.tolist()         \n    #print(acoess[0:10])\n    return sorted(acoess) #só preciso dos nomes das ações filtradas pelo preço e volume\n\n\n\ndef download_price_history(tickers: Iterable[str],\n                           start: str,\n                           end: str,\n                           group_by_ticker: bool = False,\n                           auto_adjust: bool = False,\n                           progress: bool = False) -> pd.DataFrame:\n    \"\"\"\n    Baixa o histórico de preços dos ativos via yfinance.\n\n    Parâmetros\n    ----------\n    tickers : Iterable[str]\n        Lista de tickers no padrão yfinance (ex.: PETR4.SA).\n\n    start : str\n        Data inicial (YYYY-MM-DD).\n\n    end : str\n        Data final (YYYY-MM-DD).\n\n    group_by_ticker : bool, default=False\n        Se True, retorna colunas agrupadas por ticker.\n\n    auto_adjust : bool, default=False\n        Se True, ajusta preços automaticamente (dividendos/splits).\n\n    progress : bool, default=False\n        Exibe barra de progresso do yfinance.\n\n    Retorno\n    -------\n    pandas.DataFrame\n        DataFrame com dados OHLCV.\n        Pode ser multi-indexado, dependendo do parâmetro group_by_ticker.\n    \"\"\"\n    if not tickers:\n        raise ValueError(\"A lista de tickers está vazia.\")\n\n    df = yf.download(tickers=list(tickers),\n                     start=start,\n                     end=end,\n                     auto_adjust=auto_adjust,\n                     group_by=\"column\",\n                     multi_level_index=False, #mantem df simples, sem multinivel\n                     progress=progress)\n\n    if df.empty:\n        raise RuntimeError(\"Nenhum dado retornado pelo yfinance.\")\n\n    #debug\n    #print(\"====DEBUG====\")\n    #print(df.columns)\n    return df\n\n\ndef get_asset_metadata(tickers: Iterable[str],\n                       fields: Optional[Iterable[str]] = None) -> pd.DataFrame:\n    \"\"\"\n    Obtém metadados dos ativos via yfinance.\n\n    Parâmetros\n    ----------\n    tickers : Iterable[str]\n        Lista de tickers.\n\n    fields : Iterable[str], optional\n        Campos desejados. Se None, usa um conjunto padrão.\n\n    Retorno\n    -------\n    pandas.DataFrame\n        DataFrame tabular com metadados dos ativos.\n    \"\"\"\n    default_fields = (\"longName\", \"sector\", \"industry\", \"marketCap\",\n                      \"fiftyTwoWeekHigh\", \"fiftyTwoWeekLow\", \"currency\",\n                      \"exchange\")\n\n    fields = fields or default_fields\n\n    records = []\n\n    for ticker in tickers:\n        try:\n            info = yf.Ticker(ticker).info\n        except Exception:\n            continue\n\n        record = {\"ticker\": ticker}\n\n        for field in fields:\n            record[field] = info.get(field)\n\n        records.append(record)\n\n    if not records:\n        raise RuntimeError(\"Nenhum metadado foi obtido.\")\n\n    return pd.DataFrame.from_records(records)\n\n\n\n\ndef get_price_history(\n    tickers: Iterable[str],\n    period_months: int,\n    reference_date: str | None = None,\n    group_by_ticker: bool = False,\n    auto_adjust: bool = False\n) -> pd.DataFrame:\n    \"\"\"\n    Função de alto nível para obter histórico de preços a partir de um período em meses.\n\n    Esta função é um adaptador entre o pipeline e o yfinance.\n    \"\"\"\n\n    if reference_date:\n        end_date = datetime.strptime(reference_date, \"%Y-%m-%d\")\n    else:\n        end_date = datetime.today()\n\n    start_date = end_date - relativedelta(months=period_months)\n\n    return download_price_history(\n        tickers=tickers,\n        start=start_date.strftime(\"%Y-%m-%d\"),\n        end=end_date.strftime(\"%Y-%m-%d\"),\n        group_by_ticker=group_by_ticker,\n        auto_adjust=auto_adjust,\n        progress=True\n    )\n\ndef normalize_price_columns(df: pd.DataFrame) -> pd.DataFrame:\n    \"\"\"\n    Garante que o DataFrame de preços tenha colunas MultiIndex nomeadas\n    como ('Field', 'Ticker').\n    \"\"\"\n    if not isinstance(df.columns, pd.MultiIndex):\n        raise ValueError(\"Esperado DataFrame com colunas MultiIndex.\")\n\n    if df.columns.names != [\"Field\", \"Ticker\"]:\n        df.columns = df.columns.set_names([\"Field\", \"Ticker\"])\n\n    return df\n\n\ndef generate_theoretical_dates(\n    reference_date: str | pd.Timestamp,\n    periods: int = 6,\n    spacing_days: int = 30\n) -> list[pd.Timestamp]:\n    \"\"\"\n    Gera datas teóricas espaçadas aproximadamente em meses,\n    incluindo a data de referência.\n    \"\"\"\n    if isinstance(reference_date, str):\n        reference_date = pd.Timestamp(reference_date)\n\n    return [\n        reference_date - pd.Timedelta(days=i * spacing_days)\n        for i in range(periods)\n    ]\n\ndef get_download_window(\n    theoretical_dates: list[pd.Timestamp]\n) -> tuple[pd.Timestamp, pd.Timestamp]:\n    \"\"\"\n    Retorna o intervalo mínimo necessário para download.\n    \"\"\"\n    return min(theoretical_dates), max(theoretical_dates)\n\n\n\n\ndef enrich_with_metadata_and_52w_high(\n    df: pd.DataFrame,\n    ticker_column: str = \"ticker\",\n    history_period: Literal[\"1y\"] = \"1y\",\n    high_col_name: str = \"high_52w\",\n) -> pd.DataFrame:\n    \"\"\"\n    Adiciona metadados e o preço máximo das últimas 52 semanas a um DataFrame.\n\n    Parâmetros\n    ----------\n    df\n        DataFrame que contém a coluna de tickers e já possui indicadores calculados.\n    ticker_column\n        Nome da coluna do DataFrame que contém os tickers.\n    history_period\n        Período usado para baixar o histórico de preço (deve cobrir as últimas 52 semanas).\n        '1y' é suportado pela yfinance 1.2.0.\n    high_col_name\n        Nome da coluna que conterá o máximo das últimas 52 semanas.\n\n    Retorna\n    -------\n    pd.DataFrame\n        Uma cópia do DataFrame original, com colunas extras:\n        - industry\n        - sector\n        - symbol\n        - shortName\n        - high_52w\n    \"\"\"\n    enriched_rows = []\n\n    for ticker in df[ticker_column].unique():\n        # cria objeto yfinance\n        yf_ticker = yf.Ticker(ticker)\n\n        # metadados\n        info = yf_ticker.info\n\n        industry = info.get(\"industry\")\n        sector = info.get(\"sector\")\n        symbol = info.get(\"symbol\")\n        short_name = info.get(\"shortName\")\n\n        # histórico 1 ano para extrair high de 52 semanas\n        hist = yf_ticker.history(period=history_period, auto_adjust=True)\n\n        # extrai máximo; se não houver dados, deixa como NaN\n        high_52w = (\n            hist[\"High\"].max() if \"High\" in hist.columns and not hist.empty else None\n        )\n\n        enriched_rows.append(\n            {\n                \"ticker\": ticker,\n                \"industry\": industry,\n                \"sector\": sector,\n                \"symbol\": symbol,\n                \"shortName\": short_name,\n                high_col_name: high_52w,\n            }\n        )\n\n    # transforma em DataFrame de metadados\n    metadata_df = pd.DataFrame(enriched_rows)\n    \n    \n\n    # faz join com df original\n    df_enriched = df.merge(metadata_df, how=\"left\", on=\"ticker\") #não junta porque em um df está 'ticker' e no outro está 'Ticker'\n    \n    #debug\n    #print(\"dataframe enriquecido:\")\n    #print(df_enriched)\n    #print(df_enriched.columns)\n    \n\n    return df_enriched\n"
}
```

## Assistant

<thinking>
Now I have a clear picture. Let me map the fields needed for the scatter plot:

1. `distancia` - ✅ calculated in `calculate_risk_return_indicators` (distance to 52w high as %)
2. `Risco_%` - ✅ calculated in `calculate_risk_return_indicators` (stop loss risk %)
3. `sector` - ✅ added by `enrich_with_metadata_and_52w_high`
4. `Acao` - ❌ not in ranking payload (it's `ticker`, not `Acao`)


5. `Retorno_Risco` - ✅ calculated in `calculate_risk_return_indicators`

All the required data is already in the ranking result, I just need to map `ticker` instead of `Acao` for the text labels, and use `distancia` for x-axis, `Risco_%` for y-axis, `sector` for colors, and `Retorno_Risco` for hover information.

Now I'm planning the implementation: I'll add a `build_scatter_chart_payload()` function to handle the ranking data and create Plotly scatter traces grouped by sector with quadrant reference lines, then expose it through a new `/api/scatterchart` endpoint, and finally build the corresponding frontend component to render it. Looking at the HTML structure to see where the scatter chart div should fit in the existing layout.
</thinking>

Tenho o mapa completo. Deixa eu ver o template HTML antes de escrever qualquer coisa:

**Tool Call: List the `C:\Users\Bruno\trend\ui\templates` directory's contents**
Status: Completed


# Files:
trend\ui\templates\index.html
trend\ui\templates\test_fr_chart.html


**Tool Call: Read file `ui\templates\index.html`**
Status: Completed

```json
{
  "Text": "<!DOCTYPE html>\n<html lang=\"pt-BR\">\n<head>\n    <meta charset=\"UTF-8\">\n    <title>Trend Following – Validação FR</title>\n\n    <!-- Plotly -->\n    <script src=\"https://cdn.plot.ly/plotly-2.30.0.min.js\"></script>\n\t\n\t<link href=\"https://unpkg.com/gridjs/dist/theme/mermaid.min.css\" rel=\"stylesheet\" />\n\t<script src=\"https://unpkg.com/gridjs/dist/gridjs.umd.js\"></script>\n\n    <style>\n        body {\n            font-family: Arial, sans-serif;\n            margin: 20px;\n        }\n\n        .controls {\n            margin-bottom: 20px;\n        }\n\n        #chart {\n            width: 100%;\n            height: 600px;\n        }\n\t\t\n\t\t/* Estilização do cabeçalho diferente das linhas */\n\t\t.gridjs-th {\n\t\t\tbackground-color: #222;\n\t\t\tcolor: #fff;\n\t\t\tfont-weight: 600;\n\t\t\ttext-transform: uppercase;\n\t\t\tfont-size: 0.9rem;\n\t\t}\n\n\t\t/* Destaque da linha selecionada */\n\t\t.gridjs-tr.selected .gridjs-td {\n\t\t\tbackground-color: #fff3cd; /* amarelo claro */\n\t\t}\n\n\t\t/* Ajuste visual das células (ex.: alinhamento) */\n\t\t.gridjs-td {\n\t\t\tpadding: 8px 10px;\n\t\t\tfont-size: 0.9rem;\n\t\t}\n\n\t\t/* Container da tabela */\n\t\t#table {\n\t\t\tmargin-top: 20px;\n\t\t}\n    </style>\n</head>\n<body>\n\n    <h2>Validação da Força Relativa (FR)</h2>\n\n    <div class=\"controls\">\n        <label for=\"referenceDate\">Data de referência:</label>\n        <input type=\"date\" id=\"referenceDate\">\n\n        <button onclick=\"runPipeline()\">Run</button>\n    </div>\n\n    <div id=\"chart\"></div>\n\t\n\t<div id=\"table\"></div>\n\t\n\t<div id=\"candlechart\"></div>\n\t\n\t<script src=\"/static/js/candlechart.js\"></script>\n\t<script src=\"/static/js/table.js\"></script>\n    <script src=\"/static/js/fr_chart.js\"></script>\n\n</body>\n</html>\n"
}
```

**Tool Call: Read file `ui\static\js\candlechart.js`**
Status: Completed

```json
{
  "Text": "// /static/js/candlechart.js\n// Renderização do gráfico de candlestick a partir do ticker selecionado na tabela\n\n(function () {\n    const containerId = \"candlechart\";\n\n    /**\n     * Renderiza o gráfico de candles usando Plotly\n     */\n    function renderCandleChart(payload) {\n        if (!payload || !payload.data || !payload.layout) {\n            console.error(\"Payload inválido para candlechart:\", payload);\n            return;\n        }\n\n        Plotly.newPlot(\n            containerId,\n            payload.data,\n            payload.layout,\n            { responsive: true }\n        );\n    }\n\n    /**\n     * Chama o endpoint /api/candlechart passando o ticker selecionado\n     */\n    async function fetchCandleChart(ticker) {\n        if (!ticker) return;\n\n        const url = `/api/candlechart?ticker=${encodeURIComponent(ticker)}`;\n\n        try {\n            const response = await fetch(url);\n            if (!response.ok) {\n                throw new Error(`Erro HTTP ${response.status}`);\n            }\n\n            const payload = await response.json();\n            renderCandleChart(payload);\n\n        } catch (error) {\n            console.error(\"Erro ao carregar candlechart:\", error);\n            alert(\"Erro ao gerar o gráfico de candles.\");\n        }\n    }\n\n    /**\n     * Listener do evento customizado disparado pelo table.js\n     * Espera receber { detail: { ticker: \"PETR4\" } }\n     */\n    document.addEventListener(\"DOMContentLoaded\", () => {\n        const tableContainer = document.getElementById(\"table\");\n\n        if (!tableContainer) {\n            console.warn(\"Container da tabela não encontrado\");\n            return;\n        }\n\n        tableContainer.addEventListener(\"fr:rowSelected\", (event) => {\n            const rowData = event.detail || {};\n            const ticker = rowData.ticker;\n\n            if (!ticker) {\n                console.warn(\"Ticker não encontrado no evento:\", rowData);\n                return;\n            }\n\n            console.log(\"Gerando candlechart para:\", ticker);\n            fetchCandleChart(ticker);\n        });\n    });\n\n})();"
}
```

## Assistant

<thinking>
Now I have the complete picture. Let me plan the implementation:

**Data source**: The `ranking_repository` already contains all the data needed for the scatter chart. Each item in `result["ranking"]` has:
- `distancia` ✅ (from `calculate_risk_return_indicators`)
- `Risco_%` ✅ (from `calculate_risk_return_indicators`)
- `sector` ✅ (from `enrich_with_metadata_and_52w_high`)
- `ticker` ✅ (was `Acao` in old code)
- `Retorno_Risco` ✅ (from `calculate_risk_return_indicators`)


- 
I'll need to create a builder function in the chart module, add an API endpoint that feeds from the ranking repository, and then set up the frontend to render the scatter chart after the pipeline completes. The chart should be positioned below the candlestick chart in the template.

For the event flow, I'm thinking the cleanest approach is to dispatch a custom event from `fr_chart.js` after the ranking is ready, so `scatterchart.js` can listen for it and make the API call independently—this keeps the concerns separated rather than having `fr_chart.js` directly orchestrate multiple chart renders. Building the scatter chart payload... Now I need to add the scatter chart container to the HTML file and include the JavaScript file, then implement the payload builder function that converts the ranking data into traces grouped by sector, filtering out any missing values.

Building the payload function... Building the scatter plot traces... Adding quadrant divider lines...

I'm setting up the chart layout with Portuguese labels for the axes and title, configuring the legend to display sector information vertically, and then returning the formatted data and layout for Plotly. The endpoint will be straightforward—just pulling from the ranking repository and passing it to the chart builder. On the frontend, the JavaScript will listen for ranking updates and render the scatter chart accordingly.
</thinking>

Tenho tudo o que preciso. Deixa eu mapear claramente antes de implementar:

**Fonte de dados**: `ranking_repository.get(reference_date)["ranking"]` — cada item já contém `distancia`, `Risco_%`, `sector`, `ticker` e `Retorno_Risco`, todos calculados em `calculate_risk_return_indicators` e `enrich_with_metadata_and_52w_high`.

**Plano:**
1. Adicionar `build_scatter_chart_payload()` em `chart_builders.py`
2. Adicionar endpoint `/api/scatterchart` em `routes.py` — leitura pura do cache, zero recomputação
3. Criar `scatterchart.js` — ouve evento `fr:rankingReady`, renderiza no container
4. Atualizar `fr_chart.js` — disparar `fr:rankingReady` após o ranking estar disponível
5. Atualizar `index.html` — adicionar container e script

---

### 1 — `build_scatter_chart_payload` em `chart_builders.py`

**Tool Call: app\charts\chart_builders.py**
Status: Completed

Diff: C:\Users\Bruno\trend\app\charts\chart_builders.py
```
"""
chart_builders.py

Responsável pela montagem de payloads Plotly prontos para consumo pelo frontend.

Responsabilidades:
- receber DataFrames já calculados (preços, indicadores, ranking)
- estruturar traces e layouts no formato esperado pelo Plotly JS
- retornar dicts serializáveis (JSON-safe)

Este módulo NÃO:
- baixa dados de mercado
- calcula indicadores técnicos
- executa scoring ou ranking
- conhece endpoints ou detalhes de HTTP
"""

from typing import Any, Dict, List

import numpy as np
import pandas as pd

import app.config as config
from app.data.preprocessing import build_plotly_payload, build_price_matrix_for_chart

# ===========================================================================
# Gráfico 1 — Força Relativa (linha por ativo ranqueado)
# ===========================================================================


def build_fr_chart_payload(
    price_snapshots: pd.DataFrame,
    ranking: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Monta o payload Plotly para o gráfico de validação da Força Relativa.

    Parâmetros
    ----------
    price_snapshots : pd.DataFrame
        DataFrame MultiIndex (Field, Ticker) com snapshots de preço
        nas datas resolvidas, produzido por build_ranking_result.
    ranking : list[dict]
        Lista de ativos ranqueados retornada por build_ranking_result,
        cada item contendo ao menos as chaves "ticker" e "FR_rank".

    Retorno
    -------
    dict com as chaves:
    - "data"   : list[dict] — traces Plotly
    - "layout" : dict       — configuração do layout Plotly
    """

    if price_snapshots is None or (
        hasattr(price_snapshots, "empty") and price_snapshots.empty
    ):
        raise ValueError("price_snapshots está vazio ou None")

    if not ranking:
        raise ValueError("ranking está vazio")

    # ------------------------------------------------------------------
    # Filtra tickers que atendem ao critério mínimo de FR_rank
    # ------------------------------------------------------------------
    selected_tickers = [
        item["ticker"] for item in ranking if item.get("FR_rank", 0) >= config.MIN_FR
    ]

    if not selected_tickers:
        raise ValueError(
            f"Nenhum ativo atende ao critério mínimo de FR_rank >= {config.MIN_FR}"
        )

    # ------------------------------------------------------------------
    # Monta matriz de preços (ticker × datas) para o gráfico
    # ------------------------------------------------------------------
    df_chart = build_price_matrix_for_chart(
        price_snapshots=price_snapshots,
        selected_tickers=selected_tickers,
        price_field="Adj Close",
    )

    # ------------------------------------------------------------------
    # Converte para traces Plotly
    # ------------------------------------------------------------------
    plotly_data = build_plotly_payload(df_chart)

    layout = {
        "title": "Validação da Força Relativa (FR)",
        "xaxis": {
            "title": "Data",
            "type": "date",
        },
        "yaxis": {
            "title": "Preço Ajustado (Adj Close)",
            "tickformat": ".2f",
        },
        "hovermode": "closest",
        "legend": {
            "orientation": "h",
            "y": -0.3,
        },
    }

    return {
        "data": plotly_data,
        "layout": layout,
    }


# ===========================================================================
# Gráfico 2 — Candlestick (ativo selecionado na tabela)
# ===========================================================================


def build_candle_chart_payload(
    df_ticker: pd.DataFrame,
    ticker: str,
    start_idx: int = 20,
) -> Dict[str, Any]:
    """
    Monta o payload Plotly para o gráfico de candlestick de um ativo específico.

    Parâmetros
    ----------
    df_ticker : pd.DataFrame
        Slice do histórico referente ao ativo, com índice DatetimeIndex e colunas:
        Open, High, Low, Close, Volume, Adj Close, SMA_20, BB_UPPER_20,
        BB_LOWER_20, MACD_12_26, MACD_SIGNAL_9, MACD_HIST_12_26_9,
        STOP_ATR_14_1.5.
        Deve já conter a coluna "volume_medio" calculada externamente.
    ticker : str
        Símbolo do ativo (ex.: "PETR4").
    start_idx : int
        Quantidade de linhas iniciais a descartar para eliminar o período
        sem indicadores calculados. Default: 20.

    Retorno
    -------
    dict com as chaves:
    - "data"   : list[dict] — traces Plotly
    - "layout" : dict       — configuração do layout Plotly
    """

    if df_ticker is None or df_ticker.empty:
        raise ValueError(f"DataFrame vazio recebido para o ticker {ticker!r}")

    # ------------------------------------------------------------------
    # Prepara o slice final (ordenado, sem período sem indicadores)
    # ------------------------------------------------------------------
    df_plot = df_ticker.sort_index().iloc[start_idx:]

    # Eixo temporal e séries numéricas
    datas = df_plot.index.to_pydatetime().tolist()
    open_prices = df_plot["Open"].astype(float).tolist()
    high_prices = df_plot["High"].astype(float).tolist()
    low_prices = df_plot["Low"].astype(float).tolist()
    close_prices = df_plot["Close"].astype(float).tolist()
    volume = df_plot["Volume"].tolist()
    volume_medio = df_plot["volume_medio"].tolist()

    # Cores de volume: verde se fechamento > abertura, vermelho caso contrário
    volume_colors = [
        "green" if c > o else "red" for o, c in zip(open_prices, close_prices)
    ]

    # ------------------------------------------------------------------
    # Montagem das traces
    # ------------------------------------------------------------------
    plotly_data = []

    # Candlestick principal
    plotly_data.append(
        {
            "type": "candlestick",
            "x": datas,
            "open": open_prices,
            "high": high_prices,
            "low": low_prices,
            "close": close_prices,
            "name": ticker,
            "yaxis": "y",
        }
    )

    # Média Móvel Simples
    plotly_data.append(
        {
            "type": "scatter",
            "mode": "lines",
            "x": datas,
            "y": df_plot["SMA_20"].astype(float).tolist(),
            "name": "SMA 20",
            "line": {"color": "black"},
            "yaxis": "y",
        }
    )

    # Banda Superior de Bollinger
    plotly_data.append(
        {
            "type": "scatter",
            "mode": "lines",
            "x": datas,
            "y": df_plot["BB_UPPER_20"].astype(float).tolist(),
            "name": "Upper Band",
            "line": {"dash": "dash", "color": "gray"},
            "opacity": 0.5,
            "yaxis": "y",
        }
    )

    # Banda Inferior de Bollinger (com preenchimento até a banda superior)
    plotly_data.append(
        {
            "type": "scatter",
            "mode": "lines",
            "x": datas,
            "y": df_plot["BB_LOWER_20"].astype(float).tolist(),
            "name": "Lower Band",
            "line": {"dash": "dash", "color": "gray"},
            "fill": "tonexty",
            "opacity": 0.5,
            "yaxis": "y",
        }
    )

    # STOP ATR
    plotly_data.append(
        {
            "type": "scatter",
            "mode": "lines",
            "x": datas,
            "y": df_plot["STOP_ATR_14_1.5"].tolist(),
            "name": "STOP ATR",
            "line": {"shape": "hv", "color": "red"},
            "yaxis": "y",
        }
    )

    # Volume (barras)
    plotly_data.append(
        {
            "type": "bar",
            "x": datas,
            "y": volume,
            "marker": {"color": volume_colors},
            "name": "Volume",
            "yaxis": "y2",
            "showlegend": False,
        }
    )

    # Volume Médio (linha)
    plotly_data.append(
        {
            "type": "scatter",
            "mode": "lines",
            "x": datas,
            "y": volume_medio,
            "name": "Volume Médio",
            "line": {"color": "blue"},
            "yaxis": "y2",
        }
    )

    # MACD — linha principal
    plotly_data.append(
        {
            "type": "scatter",
            "mode": "lines",
            "x": datas,
            "y": df_plot["MACD_12_26"].tolist(),
            "name": "MACD",
            "line": {"color": "black"},
            "yaxis": "y3",
        }
    )

    # MACD — linha de sinal
    plotly_data.append(
        {
            "type": "scatter",
            "mode": "lines",
            "x": datas,
            "y": df_plot["MACD_SIGNAL_9"].tolist(),
            "name": "MACD Signal",
            "line": {"dash": "dash", "color": "gray"},
            "opacity": 0.5,
            "yaxis": "y3",
        }
    )

    # MACD — histograma
    plotly_data.append(
        {
            "type": "bar",
            "x": datas,
            "y": df_plot["MACD_HIST_12_26_9"].tolist(),
            "name": "MACD Hist",
            "marker": {"color": "gray"},
            "yaxis": "y3",
        }
    )

    # ------------------------------------------------------------------
    # Layout com subplots verticais
    # ------------------------------------------------------------------
    layout = {
        "height": 650,
        "title": f"Candlestick — {ticker}",
        "xaxis": {
            "title": "Data",
            "type": "date",
            "rangeslider": {"visible": False},
            "rangebreaks": [{"bounds": ["sat", "mon"]}],
        },
        "yaxis": {  # Candlestick + indicadores de preço
            "title": "Preço",
            "domain": [0.3, 1],
            "autorange": True,
            "rangemode": "normal",
        },
        "yaxis2": {  # Volume
            "title": "Volume",
            "domain": [0.15, 0.3],
            "showgrid": False,
        },
        "yaxis3": {  # MACD
            "title": "MACD",
            "domain": [0, 0.15],
            "showgrid": False,
        },
        "hovermode": "x unified",
    }

    return {
        "data": plotly_data,
        "layout": layout,
    }


# ===========================================================================
# Gráfico 3 — Dispersão Risco × Distância (todos os ativos ranqueados)
# ===========================================================================


def build_scatter_chart_payload(
    ranking: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Monta o payload Plotly para o gráfico de dispersão Risco × Distância,
    colorido por setor, com linhas de quadrante.

    Fonte de dados: list[dict] retornada por build_ranking_result,
    que já contém os campos calculados por calculate_risk_return_indicators
    e enrich_with_metadata_and_52w_high.

    Campos consumidos por ativo
    ---------------------------
    - distancia    : distância percentual até o topo de 52 semanas (eixo X)
    - Risco_%      : risco percentual até o STOP ATR              (eixo Y)
    - sector       : setor de atuação (cor da série)
    - ticker       : rótulo de texto sobre o ponto
    - Retorno_Risco: relação retorno/risco (hover)

    Parâmetros
    ----------
    ranking : list[dict]
        Lista de ativos ranqueados, com os campos acima.

    Retorno
    -------
    dict com as chaves:
    - "data"   : list[dict] — traces Plotly (uma série por setor + linhas)
    - "layout" : dict       — configuração do layout Plotly
    """

    if not ranking:
        raise ValueError("ranking está vazio")

    df = pd.DataFrame(ranking)

    required_cols = ["distancia", "Risco_%", "ticker"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(
            f"Colunas obrigatórias ausentes no ranking: {missing}. "
            "Verifique se calculate_risk_return_indicators foi executado."
        )

    # Remove ativos sem os campos numéricos essenciais
    df = df.dropna(subset=["distancia", "Risco_%"])

    if df.empty:
        raise ValueError(
            "Nenhum ativo possui 'distancia' e 'Risco_%' válidos para o gráfico."
        )

    # Garante coluna de setor preenchida
    if "sector" not in df.columns:
        df["sector"] = "N/D"
    df["sector"] = df["sector"].fillna("N/D").astype(str)

    # Garante coluna de Retorno_Risco preenchida
    if "Retorno_Risco" not in df.columns:
        df["Retorno_Risco"] = np.nan
    df["Retorno_Risco"] = df["Retorno_Risco"].fillna(float("nan"))

    # ------------------------------------------------------------------
    # Pontos de corte dos quadrantes
    # ------------------------------------------------------------------
    x_min = float(df["distancia"].min())
    x_max = float(df["distancia"].max())
    y_min = float(df["Risco_%"].min())
    y_max = float(df["Risco_%"].max())

    mid_x = x_max / 2
    mid_y = y_max / 2

    # ------------------------------------------------------------------
    # Traces: uma série por setor (permite legenda interativa por cor)
    # ------------------------------------------------------------------
    plotly_data = []

    for sector in sorted(df["sector"].unique()):
        df_sector = df[df["sector"] == sector].copy()

        retorno_risco_values = [
            round(v, 2) if isinstance(v, float) and np.isfinite(v) else None
            for v in df_sector["Retorno_Risco"].tolist()
        ]

        plotly_data.append(
            {
                "type": "scatter",
                "mode": "markers+text",
                "name": sector,
                "x": df_sector["distancia"].tolist(),
                "y": df_sector["Risco_%"].tolist(),
                "text": df_sector["ticker"].tolist(),
                "textposition": "bottom right",
                "customdata": retorno_risco_values,
                "marker": {"size": 10},
                "hovertemplate": (
                    "<b>%{text}</b><br>"
                    "Distância: %{x:.2f}%<br>"
                    "Risco: %{y:.2f}%<br>"
                    "Retorno/Risco: %{customdata:.2f}"
                    "<extra>%{fullData.name}</extra>"
                ),
            }
        )

    # ------------------------------------------------------------------
    # Linha vertical — divide o eixo X no ponto médio
    # ------------------------------------------------------------------
    plotly_data.append(
        {
            "type": "scatter",
            "mode": "lines",
            "x": [mid_x, mid_x],
            "y": [y_min - 1, y_max + 1],
            "line": {"color": "red", "dash": "dash"},
            "showlegend": False,
            "hoverinfo": "skip",
        }
    )

    # ------------------------------------------------------------------
    # Linha horizontal — divide o eixo Y no ponto médio
    # ------------------------------------------------------------------
    plotly_data.append(
        {
            "type": "scatter",
            "mode": "lines",
            "x": [x_min - 1, x_max + 1],
            "y": [mid_y, mid_y],
            "line": {"color": "red", "dash": "dash"},
            "showlegend": False,
            "hoverinfo": "skip",
        }
    )

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    layout = {
        "title": "Dispersão por Setor — Risco × Distância do Topo (52 semanas)",
        "height": 500,
        "xaxis": {
            "title": "Distância até o Topo de 52 semanas (%)",
            "zeroline": False,
        },
        "yaxis": {
            "title": "Risco até o STOP ATR (%)",
            "zeroline": False,
        },
        "hovermode": "closest",
        "legend": {
            "title": {"text": "Setor"},
            "orientation": "v",
        },
    }

    return {
        "data": plotly_data,
        "layout": layout,
    }

```


## Assistant

<thinking>
I see that the diff ended in the middle of the `build_candle_chart_payload` function. Let me check what happened. It looks like the edit inserted the new function code but the closing of `build_candle_chart_payload` might have been disrupted.

Let me read the current state of the file to check.
</thinking>

Verifico o final do arquivo para garantir que está íntegro:

**Tool Call: Read file `app\charts\chart_builders.py` (lines 320-510)**
Status: Completed

```json
{
  "Text": "            \"domain\": [0.3, 1],\n            \"autorange\": True,\n            \"rangemode\": \"normal\",\n        },\n        \"yaxis2\": {  # Volume\n            \"title\": \"Volume\",\n            \"domain\": [0.15, 0.3],\n            \"showgrid\": False,\n        },\n        \"yaxis3\": {  # MACD\n            \"title\": \"MACD\",\n            \"domain\": [0, 0.15],\n            \"showgrid\": False,\n        },\n        \"hovermode\": \"x unified\",\n    }\n\n    return {\n        \"data\": plotly_data,\n        \"layout\": layout,\n    }\n\n\n# ===========================================================================\n# Gráfico 3 — Dispersão Risco × Distância (todos os ativos ranqueados)\n# ===========================================================================\n\n\ndef build_scatter_chart_payload(\n    ranking: List[Dict[str, Any]],\n) -> Dict[str, Any]:\n    \"\"\"\n    Monta o payload Plotly para o gráfico de dispersão Risco × Distância,\n    colorido por setor, com linhas de quadrante.\n\n    Fonte de dados: list[dict] retornada por build_ranking_result,\n    que já contém os campos calculados por calculate_risk_return_indicators\n    e enrich_with_metadata_and_52w_high.\n\n    Campos consumidos por ativo\n    ---------------------------\n    - distancia    : distância percentual até o topo de 52 semanas (eixo X)\n    - Risco_%      : risco percentual até o STOP ATR              (eixo Y)\n    - sector       : setor de atuação (cor da série)\n    - ticker       : rótulo de texto sobre o ponto\n    - Retorno_Risco: relação retorno/risco (hover)\n\n    Parâmetros\n    ----------\n    ranking : list[dict]\n        Lista de ativos ranqueados, com os campos acima.\n\n    Retorno\n    -------\n    dict com as chaves:\n    - \"data\"   : list[dict] — traces Plotly (uma série por setor + linhas)\n    - \"layout\" : dict       — configuração do layout Plotly\n    \"\"\"\n\n    if not ranking:\n        raise ValueError(\"ranking está vazio\")\n\n    df = pd.DataFrame(ranking)\n\n    required_cols = [\"distancia\", \"Risco_%\", \"ticker\"]\n    missing = [c for c in required_cols if c not in df.columns]\n    if missing:\n        raise ValueError(\n            f\"Colunas obrigatórias ausentes no ranking: {missing}. \"\n            \"Verifique se calculate_risk_return_indicators foi executado.\"\n        )\n\n    # Remove ativos sem os campos numéricos essenciais\n    df = df.dropna(subset=[\"distancia\", \"Risco_%\"])\n\n    if df.empty:\n        raise ValueError(\n            \"Nenhum ativo possui 'distancia' e 'Risco_%' válidos para o gráfico.\"\n        )\n\n    # Garante coluna de setor preenchida\n    if \"sector\" not in df.columns:\n        df[\"sector\"] = \"N/D\"\n    df[\"sector\"] = df[\"sector\"].fillna(\"N/D\").astype(str)\n\n    # Garante coluna de Retorno_Risco preenchida\n    if \"Retorno_Risco\" not in df.columns:\n        df[\"Retorno_Risco\"] = np.nan\n    df[\"Retorno_Risco\"] = df[\"Retorno_Risco\"].fillna(float(\"nan\"))\n\n    # ------------------------------------------------------------------\n    # Pontos de corte dos quadrantes\n    # ------------------------------------------------------------------\n    x_min = float(df[\"distancia\"].min())\n    x_max = float(df[\"distancia\"].max())\n    y_min = float(df[\"Risco_%\"].min())\n    y_max = float(df[\"Risco_%\"].max())\n\n    mid_x = x_max / 2\n    mid_y = y_max / 2\n\n    # ------------------------------------------------------------------\n    # Traces: uma série por setor (permite legenda interativa por cor)\n    # ------------------------------------------------------------------\n    plotly_data = []\n\n    for sector in sorted(df[\"sector\"].unique()):\n        df_sector = df[df[\"sector\"] == sector].copy()\n\n        retorno_risco_values = [\n            round(v, 2) if isinstance(v, float) and np.isfinite(v) else None\n            for v in df_sector[\"Retorno_Risco\"].tolist()\n        ]\n\n        plotly_data.append(\n            {\n                \"type\": \"scatter\",\n                \"mode\": \"markers+text\",\n                \"name\": sector,\n                \"x\": df_sector[\"distancia\"].tolist(),\n                \"y\": df_sector[\"Risco_%\"].tolist(),\n                \"text\": df_sector[\"ticker\"].tolist(),\n                \"textposition\": \"bottom right\",\n                \"customdata\": retorno_risco_values,\n                \"marker\": {\"size\": 10},\n                \"hovertemplate\": (\n                    \"<b>%{text}</b><br>\"\n                    \"Distância: %{x:.2f}%<br>\"\n                    \"Risco: %{y:.2f}%<br>\"\n                    \"Retorno/Risco: %{customdata:.2f}\"\n                    \"<extra>%{fullData.name}</extra>\"\n                ),\n            }\n        )\n\n    # ------------------------------------------------------------------\n    # Linha vertical — divide o eixo X no ponto médio\n    # ------------------------------------------------------------------\n    plotly_data.append(\n        {\n            \"type\": \"scatter\",\n            \"mode\": \"lines\",\n            \"x\": [mid_x, mid_x],\n            \"y\": [y_min - 1, y_max + 1],\n            \"line\": {\"color\": \"red\", \"dash\": \"dash\"},\n            \"showlegend\": False,\n            \"hoverinfo\": \"skip\",\n        }\n    )\n\n    # ------------------------------------------------------------------\n    # Linha horizontal — divide o eixo Y no ponto médio\n    # ------------------------------------------------------------------\n    plotly_data.append(\n        {\n            \"type\": \"scatter\",\n            \"mode\": \"lines\",\n            \"x\": [x_min - 1, x_max + 1],\n            \"y\": [mid_y, mid_y],\n            \"line\": {\"color\": \"red\", \"dash\": \"dash\"},\n            \"showlegend\": False,\n            \"hoverinfo\": \"skip\",\n        }\n    )\n\n    # ------------------------------------------------------------------\n    # Layout\n    # ------------------------------------------------------------------\n    layout = {\n        \"title\": \"Dispersão por Setor — Risco × Distância do Topo (52 semanas)\",\n        \"height\": 500,\n        \"xaxis\": {\n            \"title\": \"Distância até o Topo de 52 semanas (%)\",\n            \"zeroline\": False,\n        },\n        \"yaxis\": {\n            \"title\": \"Risco até o STOP ATR (%)\",\n            \"zeroline\": False,\n        },\n        \"hovermode\": \"closest\",\n        \"legend\": {\n            \"title\": {\"text\": \"Setor\"},\n            \"orientation\": \"v\",\n        },\n    }\n\n    return {\n        \"data\": plotly_data,\n        \"layout\": layout,\n    }\n"
}
```

## Assistant

Arquivo íntegro. Agora o endpoint:

---

### 2 — Endpoint `/api/scatterchart` em `routes.py`

**Tool Call: app\api\routes.py**
Status: Completed

Diff: C:\Users\Bruno\trend\app\api\routes.py
```
"""
routes.py

Camada de transporte HTTP da aplicação.

Responsabilidades:
- receber requisições HTTP e validar parâmetros de entrada
- orquestrar chamadas aos repositórios e builders (sem lógica de negócio inline)
- serializar e retornar respostas JSON

Este módulo NÃO:
- calcula indicadores técnicos
- executa scoring ou ranking
- monta payloads Plotly diretamente
"""

from datetime import date
from typing import Optional

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from app.charts.chart_builders import (
    build_candle_chart_payload,
    build_fr_chart_payload,
    build_scatter_chart_payload,
)
from app.core.init import init
from app.core.price_repository import price_repository
from app.core.ranking_pipeline import build_ranking_result
from app.core.ranking_repository import ranking_repository

router = APIRouter()


# ===========================================================================
# /api/fr-price-series
# Gráfico 1 — Força Relativa + tabela de ranking
# ===========================================================================


@router.get("/fr-price-series")
def get_fr_price_series(
    reference_date: Optional[str] = Query(
        default=None,
        description="Data de referência no formato YYYY-MM-DD",
    ),
):
    """
    Endpoint principal acionado ao clicar em "Run".

    Garante que o histórico de preços e o resultado do ranking estejam
    calculados e cacheados. Retorna o payload completo para:
    - Gráfico 1 (Força Relativa) via Plotly
    - Tabela de ranking (embutida na resposta, sem chamada adicional ao backend)

    Retorno
    -------
    {
        "data"    : list[dict]  — traces Plotly para o gráfico de FR
        "layout"  : dict        — layout Plotly
        "ranking" : list[dict]  — ativos ranqueados prontos para a tabela
    }
    """

    # Garante que reference_date seja sempre uma str concreta
    reference_date = reference_date or str(date.today())

    # ------------------------------------------------------------------
    # 1. Garante histórico de preços com indicadores (passos 1–4)
    # ------------------------------------------------------------------
    if not price_repository.has(reference_date):
        prices = init(reference_date)
        price_repository.set(reference_date, prices)

    prices = price_repository.get(reference_date)

    # ------------------------------------------------------------------
    # 2. Garante resultado do pipeline de ranking (passos 5–9)
    #    build_ranking_result é executado uma única vez por reference_date
    # ------------------------------------------------------------------
    if not ranking_repository.has(reference_date):
        result = build_ranking_result(prices=prices, reference_date=reference_date)
        ranking_repository.set(reference_date, result)

    result = ranking_repository.get(reference_date)

    ranking = result.get("ranking", [])
    price_snapshots: pd.DataFrame = result["price_snapshots"]

    if not ranking:
        raise HTTPException(
            status_code=404,
            detail="Nenhum ativo passou pelo ranking para a data de referência informada.",
        )

    # ------------------------------------------------------------------
    # 3. Monta payload Plotly para o gráfico de FR
    # ------------------------------------------------------------------
    try:
        chart_payload = build_fr_chart_payload(
            price_snapshots=price_snapshots,
            ranking=ranking,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # ------------------------------------------------------------------
    # 4. Retorna gráfico + ranking em uma única resposta
    #    O frontend (fr_chart.js) usa result.ranking diretamente,
    #    eliminando a necessidade de chamar /api/ranking separadamente.
    # ------------------------------------------------------------------
    return {
        "data": chart_payload["data"],
        "layout": chart_payload["layout"],
        "ranking": ranking,
    }


# ===========================================================================
# /api/ranking
# Leitura do ranking cacheado (sem recomputação)
# ===========================================================================


@router.get("/ranking")
def get_ranking():
    """
    Retorna o ranking cacheado da última execução.

    Não reexecuta o pipeline — apenas lê o resultado já armazenado
    no RankingRepository pelo endpoint /api/fr-price-series.

    Útil como fallback ou para acesso direto ao ranking sem o gráfico.
    """

    try:
        reference_date = ranking_repository.current_reference_date()
        result = ranking_repository.get(reference_date)
    except (RuntimeError, KeyError) as exc:
        raise HTTPException(
            status_code=404,
            detail=(
                "Nenhum ranking disponível. "
                "Execute o pipeline via /api/fr-price-series primeiro."
            ),
        ) from exc

    return result["ranking"]


# ===========================================================================
# /api/candlechart
# Gráfico 2 — Candlestick do ativo selecionado na tabela
# ===========================================================================


@router.get("/candlechart")
def get_candlechart(
    ticker: str = Query(..., description="Ticker do ativo selecionado na tabela"),
):
    """
    Gera o payload Plotly para o gráfico de candlestick de um ativo específico.

    Usa o histórico completo já cacheado no PriceRepository (inclui todos
    os indicadores técnicos calculados no passo 4 do init).

    Parâmetros
    ----------
    ticker : str
        Símbolo do ativo (ex.: PETR4). Case-insensitive.

    Retorno
    -------
    {
        "data"   : list[dict] — traces Plotly (candlestick, SMA, BBands, MACD, volume)
        "layout" : dict       — layout Plotly com subplots verticais
    }
    """

    # ------------------------------------------------------------------
    # 1. Recupera histórico de preços do cache
    # ------------------------------------------------------------------
    try:
        reference_date = price_repository.current_reference_date()
        prices = price_repository.get(reference_date)
    except (RuntimeError, KeyError) as exc:
        raise HTTPException(
            status_code=404,
            detail=(
                "Histórico de preços não encontrado. "
                "Execute o pipeline via /api/fr-price-series primeiro."
            ),
        ) from exc

    ticker = ticker.strip().upper()

    # ------------------------------------------------------------------
    # 2. Extrai slice do ativo selecionado
    # ------------------------------------------------------------------
    try:
        df_ticker = prices.xs(ticker, level="Ticker", axis=1).copy()
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"Ticker {ticker!r} não encontrado no histórico carregado.",
        )

    if df_ticker.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Ticker {ticker!r} não possui dados no período carregado.",
        )

    # Indicador de volume médio calculado aqui pois é específico da visualização
    df_ticker["volume_medio"] = df_ticker["Volume"].rolling(window=20).mean()

    # ------------------------------------------------------------------
    # 3. Delega montagem do payload ao chart builder
    # ------------------------------------------------------------------
    try:
        chart_payload = build_candle_chart_payload(df_ticker=df_ticker, ticker=ticker)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return chart_payload


# ===========================================================================
# /api/scatterchart
# Gráfico 3 — Dispersão Risco × Distância (todos os ativos ranqueados)
# ===========================================================================


@router.get("/scatterchart")
def get_scatterchart():
    """
    Retorna o payload Plotly para o gráfico de dispersão Risco × Distância,
    colorido por setor, com linhas de quadrante.

    Usa exclusivamente o ranking já cacheado no RankingRepository —
    nenhuma recomputação é realizada.

    O gráfico exibe todos os ativos ranqueados e é renderizado uma única vez,
    imediatamente após o pipeline ser concluído via /api/fr-price-series.

    Retorno
    -------
    {
        "data"   : list[dict] — traces Plotly (uma série por setor + linhas)
        "layout" : dict       — configuração do layout Plotly
    }
    """

    # ------------------------------------------------------------------
    # 1. Recupera o ranking cacheado
    # ------------------------------------------------------------------
    try:
        reference_date = ranking_repository.current_reference_date()
        result = ranking_repository.get(reference_date)
    except (RuntimeError, KeyError) as exc:
        raise HTTPException(
            status_code=404,
            detail=(
                "Nenhum ranking disponível. "
                "Execute o pipeline via /api/fr-price-series primeiro."
            ),
        ) from exc

    ranking = result.get("ranking", [])
    if not ranking:
        raise HTTPException(
            status_code=404,
            detail="Ranking vazio — nenhum ativo disponível para o gráfico de dispersão.",
        )

    # ------------------------------------------------------------------
    # 2. Delega montagem do payload ao chart builder
    # ------------------------------------------------------------------
    try:
        chart_payload = build_scatter_chart_payload(ranking=ranking)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return chart_payload

```


## Assistant

<thinking>
It seems the edit removed the existing `return chart_payload` at the end of `/api/candlechart` and merged it with the new endpoint in a weird way. Let me check the current state.
</thinking>

Verifico se o arquivo ficou correto:

**Tool Call: Read file `app\api\routes.py` (lines 210-285)**
Status: Completed

```json
{
  "Text": "        raise HTTPException(\n            status_code=404,\n            detail=f\"Ticker {ticker!r} não possui dados no período carregado.\",\n        )\n\n    # Indicador de volume médio calculado aqui pois é específico da visualização\n    df_ticker[\"volume_medio\"] = df_ticker[\"Volume\"].rolling(window=20).mean()\n\n    # ------------------------------------------------------------------\n    # 3. Delega montagem do payload ao chart builder\n    # ------------------------------------------------------------------\n    try:\n        chart_payload = build_candle_chart_payload(df_ticker=df_ticker, ticker=ticker)\n    except ValueError as exc:\n        raise HTTPException(status_code=422, detail=str(exc)) from exc\n\n    return chart_payload\n\n\n# ===========================================================================\n# /api/scatterchart\n# Gráfico 3 — Dispersão Risco × Distância (todos os ativos ranqueados)\n# ===========================================================================\n\n\n@router.get(\"/scatterchart\")\ndef get_scatterchart():\n    \"\"\"\n    Retorna o payload Plotly para o gráfico de dispersão Risco × Distância,\n    colorido por setor, com linhas de quadrante.\n\n    Usa exclusivamente o ranking já cacheado no RankingRepository —\n    nenhuma recomputação é realizada.\n\n    O gráfico exibe todos os ativos ranqueados e é renderizado uma única vez,\n    imediatamente após o pipeline ser concluído via /api/fr-price-series.\n\n    Retorno\n    -------\n    {\n        \"data\"   : list[dict] — traces Plotly (uma série por setor + linhas)\n        \"layout\" : dict       — configuração do layout Plotly\n    }\n    \"\"\"\n\n    # ------------------------------------------------------------------\n    # 1. Recupera o ranking cacheado\n    # ------------------------------------------------------------------\n    try:\n        reference_date = ranking_repository.current_reference_date()\n        result = ranking_repository.get(reference_date)\n    except (RuntimeError, KeyError) as exc:\n        raise HTTPException(\n            status_code=404,\n            detail=(\n                \"Nenhum ranking disponível. \"\n                \"Execute o pipeline via /api/fr-price-series primeiro.\"\n            ),\n        ) from exc\n\n    ranking = result.get(\"ranking\", [])\n    if not ranking:\n        raise HTTPException(\n            status_code=404,\n            detail=\"Ranking vazio — nenhum ativo disponível para o gráfico de dispersão.\",\n        )\n\n    # ------------------------------------------------------------------\n    # 2. Delega montagem do payload ao chart builder\n    # ------------------------------------------------------------------\n    try:\n        chart_payload = build_scatter_chart_payload(ranking=ranking)\n    except ValueError as exc:\n        raise HTTPException(status_code=422, detail=str(exc)) from exc\n\n    return chart_payload\n"
}
```

## Assistant

Perfeito. Agora o frontend:

---

### 3 — `scatterchart.js`

**Tool Call: ui\static\js\scatterchart.js**
Status: Completed

Diff: C:\Users\Bruno\trend\ui\static\js\scatterchart.js
```
// /static/js/scatterchart.js
// Gráfico de dispersão Risco × Distância do Topo (52 semanas)
//
// Ciclo de vida:
//   1. Aguarda o evento customizado "fr:rankingReady" disparado por fr_chart.js
//      após o pipeline ser concluído.
//   2. Chama GET /api/scatterchart (leitura pura do cache — zero recomputação).
//   3. Renderiza o payload Plotly no container #scatterchart.

(function () {
    const CONTAINER_ID = "scatterchart";
    const ENDPOINT = "/api/scatterchart";

    // -----------------------------------------------------------------------
    // Renderização
    // -----------------------------------------------------------------------

    function renderScatterChart(payload) {
        if (!payload || !payload.data || !payload.layout) {
            console.error("[scatterchart] Payload inválido:", payload);
            return;
        }

        const container = document.getElementById(CONTAINER_ID);
        if (!container) {
            console.warn("[scatterchart] Container #" + CONTAINER_ID + " não encontrado no DOM.");
            return;
        }

        Plotly.newPlot(
            CONTAINER_ID,
            payload.data,
            payload.layout,
            { responsive: true }
        );
    }

    // -----------------------------------------------------------------------
    // Fetch do endpoint
    // -----------------------------------------------------------------------

    async function fetchScatterChart() {
        const container = document.getElementById(CONTAINER_ID);
        if (container) {
            container.innerHTML = '<p style="color: gray; padding: 10px;">Carregando gráfico de dispersão...</p>';
        }

        try {
            const response = await fetch(ENDPOINT);

            if (!response.ok) {
                const errorBody = await response.json().catch(() => null);
                const detail = errorBody?.detail || `HTTP ${response.status}`;
                throw new Error(detail);
            }

            const payload = await response.json();
            renderScatterChart(payload);

        } catch (error) {
            console.error("[scatterchart] Erro ao carregar gráfico de dispersão:", error);

            const container = document.getElementById(CONTAINER_ID);
            if (container) {
                container.innerHTML =
                    '<p style="color: red; padding: 10px;">Erro ao carregar gráfico de dispersão: ' +
                    error.message +
                    "</p>";
            }
        }
    }

    // -----------------------------------------------------------------------
    // Listener — aguarda o pipeline estar pronto
    // -----------------------------------------------------------------------

    document.addEventListener("DOMContentLoaded", function () {
        // O evento "fr:rankingReady" é disparado por fr_chart.js após
        // o pipeline ser concluído e o ranking estar disponível.
        document.addEventListener("fr:rankingReady", function () {
            console.log("[scatterchart] Ranking pronto — carregando gráfico de dispersão.");
            fetchScatterChart();
        });
    });

})();

```


## Assistant

---

### 4 — `fr_chart.js`: disparar `fr:rankingReady`

**Tool Call: ui\static\js\fr_chart.js**
Status: Completed

Diff: C:\Users\Bruno\trend\ui\static\js\fr_chart.js
```
async function runPipeline() {
  const dateInput = document.getElementById("referenceDate").value;

  let url = "/api/fr-price-series";
  if (dateInput) {
    url += `?reference_date=${dateInput}`;
  }

  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error("Erro ao obter dados do backend");
    }

    const result = await response.json();

    // Gráfico 1 — Força Relativa
    Plotly.newPlot("chart", result.data, result.layout, { responsive: true });

    // Tabela de ranking
    if (typeof window.renderRankingTable === "function") {
      if (result && result.ranking) {
        window.renderRankingTable(result.ranking);
      } else {
        // Fallback: busca via endpoint dedicado se ranking não vier embutido
        if (typeof window.fetchAndRenderRankingTable === "function") {
          window.fetchAndRenderRankingTable(dateInput);
        }
      }
    }

    // Gráfico 3 — Dispersão: notifica scatterchart.js que o ranking está pronto
    if (result && result.ranking) {
      document.dispatchEvent(new CustomEvent("fr:rankingReady"));
    }
  } catch (error) {
    console.error(error);
    alert("Erro ao executar o pipeline.");
  }
}

```


## Assistant

---

### 5 — `index.html`: container e script

**Tool Call: ui\templates\index.html**
Status: Completed

Diff: C:\Users\Bruno\trend\ui\templates\index.html
```
<!doctype html>
<html lang="pt-BR">
    <head>
        <meta charset="UTF-8" />
        <title>Trend Following – Validação FR</title>

        <!-- Plotly -->
        <script src="https://cdn.plot.ly/plotly-2.30.0.min.js"></script>

        <link
            href="https://unpkg.com/gridjs/dist/theme/mermaid.min.css"
            rel="stylesheet"
        />
        <script src="https://unpkg.com/gridjs/dist/gridjs.umd.js"></script>

        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 20px;
            }

            .controls {
                margin-bottom: 20px;
            }

            #chart {
                width: 100%;
                height: 600px;
            }

            /* Estilização do cabeçalho diferente das linhas */
            .gridjs-th {
                background-color: #222;
                color: #fff;
                font-weight: 600;
                text-transform: uppercase;
                font-size: 0.9rem;
            }

            /* Destaque da linha selecionada */
            .gridjs-tr.selected .gridjs-td {
                background-color: #fff3cd; /* amarelo claro */
            }

            /* Ajuste visual das células (ex.: alinhamento) */
            .gridjs-td {
                padding: 8px 10px;
                font-size: 0.9rem;
            }

            /* Container da tabela */
            #table {
                margin-top: 20px;
            }

            /* Container do gráfico de dispersão */
            #scatterchart {
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <h2>Validação da Força Relativa (FR)</h2>

        <div class="controls">
            <label for="referenceDate">Data de referência:</label>
            <input type="date" id="referenceDate" />

            <button onclick="runPipeline()">Run</button>
        </div>

        <div id="chart"></div>

        <div id="table"></div>

        <div id="candlechart"></div>

        <div id="scatterchart"></div>

        <script src="/static/js/candlechart.js"></script>
        <script src="/static/js/table.js"></script>
        <script src="/static/js/fr_chart.js"></script>
        <script src="/static/js/scatterchart.js"></script>
    </body>
</html>

```


## Assistant

Verificação final de diagnósticos:

**Tool Call: Check project diagnostics**
Status: Completed

C:\Users\Bruno\trend\app\data\market_data.py: 0 error(s), 1 warning(s)
C:\Users\Bruno\trend\app\data\market_data.py: 11 error(s), 0 warning(s)
C:\Users\Bruno\trend\app\services\ranking.py: 3 error(s), 0 warning(s)
C:\Users\Bruno\trend\app\data\preprocessing.py: 2 error(s), 2 warning(s)
C:\Users\Bruno\trend\app\data\preprocessing.py: 2 error(s), 0 warning(s)
C:\Users\Bruno\trend\app\charts\chart_builders.py: 8 error(s), 0 warning(s)
C:\Users\Bruno\trend\app\core\ranking_pipeline.py: 2 error(s), 0 warning(s)
C:\Users\Bruno\trend\app\core\init.py: 0 error(s), 15 warning(s)
C:\Users\Bruno\trend\app\core\init.py: 2 error(s), 0 warning(s)


**Tool Call: Check diagnostics for `C:\Users\Bruno\trend\app\charts\chart_builders.py`**
Status: Completed

error at line 413: Argument of type "Series | Unknown | Any" cannot be assigned to parameter "x" of type "ConvertibleToFloat" in function "__new__"
  Type "Series | Unknown | Any" is not assignable to type "ConvertibleToFloat"
    Type "Series" is not assignable to type "ConvertibleToFloat"
      "Series" is not assignable to "str"
      "Series" is incompatible with protocol "Buffer"
        "__buffer__" is not present
      "Series" is incompatible with protocol "SupportsFloat"
        "__float__" is not present
      "Series" is incompatible with protocol "SupportsIndex"
error at line 413: Argument of type "Series | Unknown | Any" cannot be assigned to parameter "x" of type "ConvertibleToFloat" in function "__new__"
  Type "Series | Unknown | Any" is not assignable to type "ConvertibleToFloat"
    Type "Series" is not assignable to type "ConvertibleToFloat"
      "Series" is not assignable to "str"
      "Series" is incompatible with protocol "Buffer"
        "__buffer__" is not present
      "Series" is incompatible with protocol "SupportsFloat"
        "__float__" is not present
      "Series" is incompatible with protocol "SupportsIndex"
  ...
error at line 414: Argument of type "Series | Unknown | Any" cannot be assigned to parameter "x" of type "ConvertibleToFloat" in function "__new__"
  Type "Series | Unknown | Any" is not assignable to type "ConvertibleToFloat"
    Type "Series" is not assignable to type "ConvertibleToFloat"
      "Series" is not assignable to "str"
      "Series" is incompatible with protocol "Buffer"
        "__buffer__" is not present
      "Series" is incompatible with protocol "SupportsFloat"
        "__float__" is not present
      "Series" is incompatible with protocol "SupportsIndex"
  ...
error at line 414: Argument of type "Series | Unknown | Any" cannot be assigned to parameter "x" of type "ConvertibleToFloat" in function "__new__"
  Type "Series | Unknown | Any" is not assignable to type "ConvertibleToFloat"
    Type "Series" is not assignable to type "ConvertibleToFloat"
      "Series" is not assignable to "str"
      "Series" is incompatible with protocol "Buffer"
        "__buffer__" is not present
      "Series" is incompatible with protocol "SupportsFloat"
        "__float__" is not present
      "Series" is incompatible with protocol "SupportsIndex"
error at line 415: Argument of type "Series | Unknown | Any" cannot be assigned to parameter "x" of type "ConvertibleToFloat" in function "__new__"
  Type "Series | Unknown | Any" is not assignable to type "ConvertibleToFloat"
    Type "Series" is not assignable to type "ConvertibleToFloat"
      "Series" is not assignable to "str"
      "Series" is incompatible with protocol "Buffer"
        "__buffer__" is not present
      "Series" is incompatible with protocol "SupportsFloat"
        "__float__" is not present
      "Series" is incompatible with protocol "SupportsIndex"
error at line 415: Argument of type "Series | Unknown | Any" cannot be assigned to parameter "x" of type "ConvertibleToFloat" in function "__new__"
  Type "Series | Unknown | Any" is not assignable to type "ConvertibleToFloat"
    Type "Series" is not assignable to type "ConvertibleToFloat"
      "Series" is not assignable to "str"
      "Series" is incompatible with protocol "Buffer"
        "__buffer__" is not present
      "Series" is incompatible with protocol "SupportsFloat"
        "__float__" is not present
      "Series" is incompatible with protocol "SupportsIndex"
  ...
error at line 416: Argument of type "Series | Unknown | Any" cannot be assigned to parameter "x" of type "ConvertibleToFloat" in function "__new__"
  Type "Series | Unknown | Any" is not assignable to type "ConvertibleToFloat"
    Type "Series" is not assignable to type "ConvertibleToFloat"
      "Series" is not assignable to "str"
      "Series" is incompatible with protocol "Buffer"
        "__buffer__" is not present
      "Series" is incompatible with protocol "SupportsFloat"
        "__float__" is not present
      "Series" is incompatible with protocol "SupportsIndex"
  ...
error at line 416: Argument of type "Series | Unknown | Any" cannot be assigned to parameter "x" of type "ConvertibleToFloat" in function "__new__"
  Type "Series | Unknown | Any" is not assignable to type "ConvertibleToFloat"
    Type "Series" is not assignable to type "ConvertibleToFloat"
      "Series" is not assignable to "str"
      "Series" is incompatible with protocol "Buffer"
        "__buffer__" is not present
      "Series" is incompatible with protocol "SupportsFloat"
        "__float__" is not present
      "Series" is incompatible with protocol "SupportsIndex"


## Assistant

<thinking>
The issue is on lines 413-416. These are likely the `float()` calls like `float(df["distancia"].min())`. The type checker is complaining because `df["distancia"].min()` can return a `Series` in some contexts (it won't at runtime, but the type checker doesn't know). I need to cast these explicitly.

Let me check lines 413-416 of the file.
</thinking>

**Tool Call: Read file `app\charts\chart_builders.py` (lines 408-422)**
Status: Completed

```json
{
  "Text": "    df[\"Retorno_Risco\"] = df[\"Retorno_Risco\"].fillna(float(\"nan\"))\n\n    # ------------------------------------------------------------------\n    # Pontos de corte dos quadrantes\n    # ------------------------------------------------------------------\n    x_min = float(df[\"distancia\"].min())\n    x_max = float(df[\"distancia\"].max())\n    y_min = float(df[\"Risco_%\"].min())\n    y_max = float(df[\"Risco_%\"].max())\n\n    mid_x = x_max / 2\n    mid_y = y_max / 2\n\n    # ------------------------------------------------------------------\n    # Traces: uma série por setor (permite legenda interativa por cor)\n"
}
```

## Assistant

<thinking>
The issue is that `df["distancia"].min()` returns `Series | Unknown | Any` which the type checker doesn't know can be passed to `float()`. I need to use `.iloc[0]` or explicitly type hint. The cleanest fix is to use `.to_numpy().min()` or just convert to numpy scalar explicitly.

Actually, the simplest fix is `float(df["distancia"].min())` - but the type checker is confused. Let me try using `df["distancia"].min().item()` or `float(df["distancia"].min().item())`.

Actually, the issue is that `pd.Series.min()` can return different types. 

I'll resolve this by accessing the underlying numpy array with `.values` and calling `.min()` and `.max()` on that instead, which gives the type checker a clearer picture of what's being returned.
</thinking>

O type checker está confuso com `pd.Series.min()` retornando um tipo genérico. Corrijo usando `.values` para extrair o escalar numpy diretamente:

**Tool Call: app\charts\chart_builders.py**
Status: Completed

Diff: C:\Users\Bruno\trend\app\charts\chart_builders.py
```
"""
chart_builders.py

Responsável pela montagem de payloads Plotly prontos para consumo pelo frontend.

Responsabilidades:
- receber DataFrames já calculados (preços, indicadores, ranking)
- estruturar traces e layouts no formato esperado pelo Plotly JS
- retornar dicts serializáveis (JSON-safe)

Este módulo NÃO:
- baixa dados de mercado
- calcula indicadores técnicos
- executa scoring ou ranking
- conhece endpoints ou detalhes de HTTP
"""

from typing import Any, Dict, List

import numpy as np
import pandas as pd

import app.config as config
from app.data.preprocessing import build_plotly_payload, build_price_matrix_for_chart

# ===========================================================================
# Gráfico 1 — Força Relativa (linha por ativo ranqueado)
# ===========================================================================


def build_fr_chart_payload(
    price_snapshots: pd.DataFrame,
    ranking: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Monta o payload Plotly para o gráfico de validação da Força Relativa.

    Parâmetros
    ----------
    price_snapshots : pd.DataFrame
        DataFrame MultiIndex (Field, Ticker) com snapshots de preço
        nas datas resolvidas, produzido por build_ranking_result.
    ranking : list[dict]
        Lista de ativos ranqueados retornada por build_ranking_result,
        cada item contendo ao menos as chaves "ticker" e "FR_rank".

    Retorno
    -------
    dict com as chaves:
    - "data"   : list[dict] — traces Plotly
    - "layout" : dict       — configuração do layout Plotly
    """

    if price_snapshots is None or (
        hasattr(price_snapshots, "empty") and price_snapshots.empty
    ):
        raise ValueError("price_snapshots está vazio ou None")

    if not ranking:
        raise ValueError("ranking está vazio")

    # ------------------------------------------------------------------
    # Filtra tickers que atendem ao critério mínimo de FR_rank
    # ------------------------------------------------------------------
    selected_tickers = [
        item["ticker"] for item in ranking if item.get("FR_rank", 0) >= config.MIN_FR
    ]

    if not selected_tickers:
        raise ValueError(
            f"Nenhum ativo atende ao critério mínimo de FR_rank >= {config.MIN_FR}"
        )

    # ------------------------------------------------------------------
    # Monta matriz de preços (ticker × datas) para o gráfico
    # ------------------------------------------------------------------
    df_chart = build_price_matrix_for_chart(
        price_snapshots=price_snapshots,
        selected_tickers=selected_tickers,
        price_field="Adj Close",
    )

    # ------------------------------------------------------------------
    # Converte para traces Plotly
    # ------------------------------------------------------------------
    plotly_data = build_plotly_payload(df_chart)

    layout = {
        "title": "Validação da Força Relativa (FR)",
        "xaxis": {
            "title": "Data",
            "type": "date",
        },
        "yaxis": {
            "title": "Preço Ajustado (Adj Close)",
            "tickformat": ".2f",
        },
        "hovermode": "closest",
        "legend": {
            "orientation": "h",
            "y": -0.3,
        },
    }

    return {
        "data": plotly_data,
        "layout": layout,
    }


# ===========================================================================
# Gráfico 2 — Candlestick (ativo selecionado na tabela)
# ===========================================================================


def build_candle_chart_payload(
    df_ticker: pd.DataFrame,
    ticker: str,
    start_idx: int = 20,
) -> Dict[str, Any]:
    """
    Monta o payload Plotly para o gráfico de candlestick de um ativo específico.

    Parâmetros
    ----------
    df_ticker : pd.DataFrame
        Slice do histórico referente ao ativo, com índice DatetimeIndex e colunas:
        Open, High, Low, Close, Volume, Adj Close, SMA_20, BB_UPPER_20,
        BB_LOWER_20, MACD_12_26, MACD_SIGNAL_9, MACD_HIST_12_26_9,
        STOP_ATR_14_1.5.
        Deve já conter a coluna "volume_medio" calculada externamente.
    ticker : str
        Símbolo do ativo (ex.: "PETR4").
    start_idx : int
        Quantidade de linhas iniciais a descartar para eliminar o período
        sem indicadores calculados. Default: 20.

    Retorno
    -------
    dict com as chaves:
    - "data"   : list[dict] — traces Plotly
    - "layout" : dict       — configuração do layout Plotly
    """

    if df_ticker is None or df_ticker.empty:
        raise ValueError(f"DataFrame vazio recebido para o ticker {ticker!r}")

    # ------------------------------------------------------------------
    # Prepara o slice final (ordenado, sem período sem indicadores)
    # ------------------------------------------------------------------
    df_plot = df_ticker.sort_index().iloc[start_idx:]

    # Eixo temporal e séries numéricas
    datas = df_plot.index.to_pydatetime().tolist()
    open_prices = df_plot["Open"].astype(float).tolist()
    high_prices = df_plot["High"].astype(float).tolist()
    low_prices = df_plot["Low"].astype(float).tolist()
    close_prices = df_plot["Close"].astype(float).tolist()
    volume = df_plot["Volume"].tolist()
    volume_medio = df_plot["volume_medio"].tolist()

    # Cores de volume: verde se fechamento > abertura, vermelho caso contrário
    volume_colors = [
        "green" if c > o else "red" for o, c in zip(open_prices, close_prices)
    ]

    # ------------------------------------------------------------------
    # Montagem das traces
    # ------------------------------------------------------------------
    plotly_data = []

    # Candlestick principal
    plotly_data.append(
        {
            "type": "candlestick",
            "x": datas,
            "open": open_prices,
            "high": high_prices,
            "low": low_prices,
            "close": close_prices,
            "name": ticker,
            "yaxis": "y",
        }
    )

    # Média Móvel Simples
    plotly_data.append(
        {
            "type": "scatter",
            "mode": "lines",
            "x": datas,
            "y": df_plot["SMA_20"].astype(float).tolist(),
            "name": "SMA 20",
            "line": {"color": "black"},
            "yaxis": "y",
        }
    )

    # Banda Superior de Bollinger
    plotly_data.append(
        {
            "type": "scatter",
            "mode": "lines",
            "x": datas,
            "y": df_plot["BB_UPPER_20"].astype(float).tolist(),
            "name": "Upper Band",
            "line": {"dash": "dash", "color": "gray"},
            "opacity": 0.5,
            "yaxis": "y",
        }
    )

    # Banda Inferior de Bollinger (com preenchimento até a banda superior)
    plotly_data.append(
        {
            "type": "scatter",
            "mode": "lines",
            "x": datas,
            "y": df_plot["BB_LOWER_20"].astype(float).tolist(),
            "name": "Lower Band",
            "line": {"dash": "dash", "color": "gray"},
            "fill": "tonexty",
            "opacity": 0.5,
            "yaxis": "y",
        }
    )

    # STOP ATR
    plotly_data.append(
        {
            "type": "scatter",
            "mode": "lines",
            "x": datas,
            "y": df_plot["STOP_ATR_14_1.5"].tolist(),
            "name": "STOP ATR",
            "line": {"shape": "hv", "color": "red"},
            "yaxis": "y",
        }
    )

    # Volume (barras)
    plotly_data.append(
        {
            "type": "bar",
            "x": datas,
            "y": volume,
            "marker": {"color": volume_colors},
            "name": "Volume",
            "yaxis": "y2",
            "showlegend": False,
        }
    )

    # Volume Médio (linha)
    plotly_data.append(
        {
            "type": "scatter",
            "mode": "lines",
            "x": datas,
            "y": volume_medio,
            "name": "Volume Médio",
            "line": {"color": "blue"},
            "yaxis": "y2",
        }
    )

    # MACD — linha principal
    plotly_data.append(
        {
            "type": "scatter",
            "mode": "lines",
            "x": datas,
            "y": df_plot["MACD_12_26"].tolist(),
            "name": "MACD",
            "line": {"color": "black"},
            "yaxis": "y3",
        }
    )

    # MACD — linha de sinal
    plotly_data.append(
        {
            "type": "scatter",
            "mode": "lines",
            "x": datas,
            "y": df_plot["MACD_SIGNAL_9"].tolist(),
            "name": "MACD Signal",
            "line": {"dash": "dash", "color": "gray"},
            "opacity": 0.5,
            "yaxis": "y3",
        }
    )

    # MACD — histograma
    plotly_data.append(
        {
            "type": "bar",
            "x": datas,
            "y": df_plot["MACD_HIST_12_26_9"].tolist(),
            "name": "MACD Hist",
            "marker": {"color": "gray"},
            "yaxis": "y3",
        }
    )

    # ------------------------------------------------------------------
    # Layout com subplots verticais
    # ------------------------------------------------------------------
    layout = {
        "height": 650,
        "title": f"Candlestick — {ticker}",
        "xaxis": {
            "title": "Data",
            "type": "date",
            "rangeslider": {"visible": False},
            "rangebreaks": [{"bounds": ["sat", "mon"]}],
        },
        "yaxis": {  # Candlestick + indicadores de preço
            "title": "Preço",
            "domain": [0.3, 1],
            "autorange": True,
            "rangemode": "normal",
        },
        "yaxis2": {  # Volume
            "title": "Volume",
            "domain": [0.15, 0.3],
            "showgrid": False,
        },
        "yaxis3": {  # MACD
            "title": "MACD",
            "domain": [0, 0.15],
            "showgrid": False,
        },
        "hovermode": "x unified",
    }

    return {
        "data": plotly_data,
        "layout": layout,
    }


# ===========================================================================
# Gráfico 3 — Dispersão Risco × Distância (todos os ativos ranqueados)
# ===========================================================================


def build_scatter_chart_payload(
    ranking: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Monta o payload Plotly para o gráfico de dispersão Risco × Distância,
    colorido por setor, com linhas de quadrante.

    Fonte de dados: list[dict] retornada por build_ranking_result,
    que já contém os campos calculados por calculate_risk_return_indicators
    e enrich_with_metadata_and_52w_high.

    Campos consumidos por ativo
    ---------------------------
    - distancia    : distância percentual até o topo de 52 semanas (eixo X)
    - Risco_%      : risco percentual até o STOP ATR              (eixo Y)
    - sector       : setor de atuação (cor da série)
    - ticker       : rótulo de texto sobre o ponto
    - Retorno_Risco: relação retorno/risco (hover)

    Parâmetros
    ----------
    ranking : list[dict]
        Lista de ativos ranqueados, com os campos acima.

    Retorno
    -------
    dict com as chaves:
    - "data"   : list[dict] — traces Plotly (uma série por setor + linhas)
    - "layout" : dict       — configuração do layout Plotly
    """

    if not ranking:
        raise ValueError("ranking está vazio")

    df = pd.DataFrame(ranking)

    required_cols = ["distancia", "Risco_%", "ticker"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(
            f"Colunas obrigatórias ausentes no ranking: {missing}. "
            "Verifique se calculate_risk_return_indicators foi executado."
        )

    # Remove ativos sem os campos numéricos essenciais
    df = df.dropna(subset=["distancia", "Risco_%"])

    if df.empty:
        raise ValueError(
            "Nenhum ativo possui 'distancia' e 'Risco_%' válidos para o gráfico."
        )

    # Garante coluna de setor preenchida
    if "sector" not in df.columns:
        df["sector"] = "N/D"
    df["sector"] = df["sector"].fillna("N/D").astype(str)

    # Garante coluna de Retorno_Risco preenchida
    if "Retorno_Risco" not in df.columns:
        df["Retorno_Risco"] = np.nan
    df["Retorno_Risco"] = df["Retorno_Risco"].fillna(float("nan"))

    # ------------------------------------------------------------------
    # Pontos de corte dos quadrantes
    # ------------------------------------------------------------------
    x_min = float(df["distancia"].values.min())
    x_max = float(df["distancia"].values.max())
    y_min = float(df["Risco_%"].values.min())
    y_max = float(df["Risco_%"].values.max())

    mid_x = x_max / 2
    mid_y = y_max / 2

    # ------------------------------------------------------------------
    # Traces: uma série por setor (permite legenda interativa por cor)
    # ------------------------------------------------------------------
    plotly_data = []

    for sector in sorted(df["sector"].unique()):
        df_sector = df[df["sector"] == sector].copy()

        retorno_risco_values = [
            round(v, 2) if isinstance(v, float) and np.isfinite(v) else None
            for v in df_sector["Retorno_Risco"].tolist()
        ]

        plotly_data.append(
            {
                "type": "scatter",
                "mode": "markers+text",
                "name": sector,
                "x": df_sector["distancia"].tolist(),
                "y": df_sector["Risco_%"].tolist(),
                "text": df_sector["ticker"].tolist(),
                "textposition": "bottom right",
                "customdata": retorno_risco_values,
                "marker": {"size": 10},
                "hovertemplate": (
                    "<b>%{text}</b><br>"
                    "Distância: %{x:.2f}%<br>"
                    "Risco: %{y:.2f}%<br>"
                    "Retorno/Risco: %{customdata:.2f}"
                    "<extra>%{fullData.name}</extra>"
                ),
            }
        )

    # ------------------------------------------------------------------
    # Linha vertical — divide o eixo X no ponto médio
    # ------------------------------------------------------------------
    plotly_data.append(
        {
            "type": "scatter",
            "mode": "lines",
            "x": [mid_x, mid_x],
            "y": [y_min - 1, y_max + 1],
            "line": {"color": "red", "dash": "dash"},
            "showlegend": False,
            "hoverinfo": "skip",
        }
    )

    # ------------------------------------------------------------------
    # Linha horizontal — divide o eixo Y no ponto médio
    # ------------------------------------------------------------------
    plotly_data.append(
        {
            "type": "scatter",
            "mode": "lines",
            "x": [x_min - 1, x_max + 1],
            "y": [mid_y, mid_y],
            "line": {"color": "red", "dash": "dash"},
            "showlegend": False,
            "hoverinfo": "skip",
        }
    )

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    layout = {
        "title": "Dispersão por Setor — Risco × Distância do Topo (52 semanas)",
        "height": 500,
        "xaxis": {
            "title": "Distância até o Topo de 52 semanas (%)",
            "zeroline": False,
        },
        "yaxis": {
            "title": "Risco até o STOP ATR (%)",
            "zeroline": False,
        },
        "hovermode": "closest",
        "legend": {
            "title": {"text": "Setor"},
            "orientation": "v",
        },
    }

    return {
        "data": plotly_data,
        "layout": layout,
    }

```


**Tool Call: Check diagnostics for `C:\Users\Bruno\trend\app\charts\chart_builders.py`**
Status: Completed

error at line 413: Cannot access attribute "min" for class "ExtensionArray"
  Attribute "min" is unknown
error at line 414: Cannot access attribute "max" for class "ExtensionArray"
  Attribute "max" is unknown
error at line 415: Cannot access attribute "min" for class "ExtensionArray"
  Attribute "min" is unknown
error at line 416: Cannot access attribute "max" for class "ExtensionArray"
  Attribute "max" is unknown


## Assistant

<thinking>
The type checker is still complaining. The issue is that `df["distancia"].values` can return `ExtensionArray | ndarray`, and `ExtensionArray` doesn't have `min`/`max` in the type stubs. Let me use `np.min()` / `np.max()` explicitly, which can handle both ndarrays and Series.

Actually, let me just use `df["distancia"].to_numpy(dtype=float).min()` - converting explicitly to numpy float array first.
</thinking>

**Tool Call: app\charts\chart_builders.py**
Status: Completed

Diff: C:\Users\Bruno\trend\app\charts\chart_builders.py
```
"""
chart_builders.py

Responsável pela montagem de payloads Plotly prontos para consumo pelo frontend.

Responsabilidades:
- receber DataFrames já calculados (preços, indicadores, ranking)
- estruturar traces e layouts no formato esperado pelo Plotly JS
- retornar dicts serializáveis (JSON-safe)

Este módulo NÃO:
- baixa dados de mercado
- calcula indicadores técnicos
- executa scoring ou ranking
- conhece endpoints ou detalhes de HTTP
"""

from typing import Any, Dict, List

import numpy as np
import pandas as pd

import app.config as config
from app.data.preprocessing import build_plotly_payload, build_price_matrix_for_chart

# ===========================================================================
# Gráfico 1 — Força Relativa (linha por ativo ranqueado)
# ===========================================================================


def build_fr_chart_payload(
    price_snapshots: pd.DataFrame,
    ranking: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Monta o payload Plotly para o gráfico de validação da Força Relativa.

    Parâmetros
    ----------
    price_snapshots : pd.DataFrame
        DataFrame MultiIndex (Field, Ticker) com snapshots de preço
        nas datas resolvidas, produzido por build_ranking_result.
    ranking : list[dict]
        Lista de ativos ranqueados retornada por build_ranking_result,
        cada item contendo ao menos as chaves "ticker" e "FR_rank".

    Retorno
    -------
    dict com as chaves:
    - "data"   : list[dict] — traces Plotly
    - "layout" : dict       — configuração do layout Plotly
    """

    if price_snapshots is None or (
        hasattr(price_snapshots, "empty") and price_snapshots.empty
    ):
        raise ValueError("price_snapshots está vazio ou None")

    if not ranking:
        raise ValueError("ranking está vazio")

    # ------------------------------------------------------------------
    # Filtra tickers que atendem ao critério mínimo de FR_rank
    # ------------------------------------------------------------------
    selected_tickers = [
        item["ticker"] for item in ranking if item.get("FR_rank", 0) >= config.MIN_FR
    ]

    if not selected_tickers:
        raise ValueError(
            f"Nenhum ativo atende ao critério mínimo de FR_rank >= {config.MIN_FR}"
        )

    # ------------------------------------------------------------------
    # Monta matriz de preços (ticker × datas) para o gráfico
    # ------------------------------------------------------------------
    df_chart = build_price_matrix_for_chart(
        price_snapshots=price_snapshots,
        selected_tickers=selected_tickers,
        price_field="Adj Close",
    )

    # ------------------------------------------------------------------
    # Converte para traces Plotly
    # ------------------------------------------------------------------
    plotly_data = build_plotly_payload(df_chart)

    layout = {
        "title": "Validação da Força Relativa (FR)",
        "xaxis": {
            "title": "Data",
            "type": "date",
        },
        "yaxis": {
            "title": "Preço Ajustado (Adj Close)",
            "tickformat": ".2f",
        },
        "hovermode": "closest",
        "legend": {
            "orientation": "h",
            "y": -0.3,
        },
    }

    return {
        "data": plotly_data,
        "layout": layout,
    }


# ===========================================================================
# Gráfico 2 — Candlestick (ativo selecionado na tabela)
# ===========================================================================


def build_candle_chart_payload(
    df_ticker: pd.DataFrame,
    ticker: str,
    start_idx: int = 20,
) -> Dict[str, Any]:
    """
    Monta o payload Plotly para o gráfico de candlestick de um ativo específico.

    Parâmetros
    ----------
    df_ticker : pd.DataFrame
        Slice do histórico referente ao ativo, com índice DatetimeIndex e colunas:
        Open, High, Low, Close, Volume, Adj Close, SMA_20, BB_UPPER_20,
        BB_LOWER_20, MACD_12_26, MACD_SIGNAL_9, MACD_HIST_12_26_9,
        STOP_ATR_14_1.5.
        Deve já conter a coluna "volume_medio" calculada externamente.
    ticker : str
        Símbolo do ativo (ex.: "PETR4").
    start_idx : int
        Quantidade de linhas iniciais a descartar para eliminar o período
        sem indicadores calculados. Default: 20.

    Retorno
    -------
    dict com as chaves:
    - "data"   : list[dict] — traces Plotly
    - "layout" : dict       — configuração do layout Plotly
    """

    if df_ticker is None or df_ticker.empty:
        raise ValueError(f"DataFrame vazio recebido para o ticker {ticker!r}")

    # ------------------------------------------------------------------
    # Prepara o slice final (ordenado, sem período sem indicadores)
    # ------------------------------------------------------------------
    df_plot = df_ticker.sort_index().iloc[start_idx:]

    # Eixo temporal e séries numéricas
    datas = df_plot.index.to_pydatetime().tolist()
    open_prices = df_plot["Open"].astype(float).tolist()
    high_prices = df_plot["High"].astype(float).tolist()
    low_prices = df_plot["Low"].astype(float).tolist()
    close_prices = df_plot["Close"].astype(float).tolist()
    volume = df_plot["Volume"].tolist()
    volume_medio = df_plot["volume_medio"].tolist()

    # Cores de volume: verde se fechamento > abertura, vermelho caso contrário
    volume_colors = [
        "green" if c > o else "red" for o, c in zip(open_prices, close_prices)
    ]

    # ------------------------------------------------------------------
    # Montagem das traces
    # ------------------------------------------------------------------
    plotly_data = []

    # Candlestick principal
    plotly_data.append(
        {
            "type": "candlestick",
            "x": datas,
            "open": open_prices,
            "high": high_prices,
            "low": low_prices,
            "close": close_prices,
            "name": ticker,
            "yaxis": "y",
        }
    )

    # Média Móvel Simples
    plotly_data.append(
        {
            "type": "scatter",
            "mode": "lines",
            "x": datas,
            "y": df_plot["SMA_20"].astype(float).tolist(),
            "name": "SMA 20",
            "line": {"color": "black"},
            "yaxis": "y",
        }
    )

    # Banda Superior de Bollinger
    plotly_data.append(
        {
            "type": "scatter",
            "mode": "lines",
            "x": datas,
            "y": df_plot["BB_UPPER_20"].astype(float).tolist(),
            "name": "Upper Band",
            "line": {"dash": "dash", "color": "gray"},
            "opacity": 0.5,
            "yaxis": "y",
        }
    )

    # Banda Inferior de Bollinger (com preenchimento até a banda superior)
    plotly_data.append(
        {
            "type": "scatter",
            "mode": "lines",
            "x": datas,
            "y": df_plot["BB_LOWER_20"].astype(float).tolist(),
            "name": "Lower Band",
            "line": {"dash": "dash", "color": "gray"},
            "fill": "tonexty",
            "opacity": 0.5,
            "yaxis": "y",
        }
    )

    # STOP ATR
    plotly_data.append(
        {
            "type": "scatter",
            "mode": "lines",
            "x": datas,
            "y": df_plot["STOP_ATR_14_1.5"].tolist(),
            "name": "STOP ATR",
            "line": {"shape": "hv", "color": "red"},
            "yaxis": "y",
        }
    )

    # Volume (barras)
    plotly_data.append(
        {
            "type": "bar",
            "x": datas,
            "y": volume,
            "marker": {"color": volume_colors},
            "name": "Volume",
            "yaxis": "y2",
            "showlegend": False,
        }
    )

    # Volume Médio (linha)
    plotly_data.append(
        {
            "type": "scatter",
            "mode": "lines",
            "x": datas,
            "y": volume_medio,
            "name": "Volume Médio",
            "line": {"color": "blue"},
            "yaxis": "y2",
        }
    )

    # MACD — linha principal
    plotly_data.append(
        {
            "type": "scatter",
            "mode": "lines",
            "x": datas,
            "y": df_plot["MACD_12_26"].tolist(),
            "name": "MACD",
            "line": {"color": "black"},
            "yaxis": "y3",
        }
    )

    # MACD — linha de sinal
    plotly_data.append(
        {
            "type": "scatter",
            "mode": "lines",
            "x": datas,
            "y": df_plot["MACD_SIGNAL_9"].tolist(),
            "name": "MACD Signal",
            "line": {"dash": "dash", "color": "gray"},
            "opacity": 0.5,
            "yaxis": "y3",
        }
    )

    # MACD — histograma
    plotly_data.append(
        {
            "type": "bar",
            "x": datas,
            "y": df_plot["MACD_HIST_12_26_9"].tolist(),
            "name": "MACD Hist",
            "marker": {"color": "gray"},
            "yaxis": "y3",
        }
    )

    # ------------------------------------------------------------------
    # Layout com subplots verticais
    # ------------------------------------------------------------------
    layout = {
        "height": 650,
        "title": f"Candlestick — {ticker}",
        "xaxis": {
            "title": "Data",
            "type": "date",
            "rangeslider": {"visible": False},
            "rangebreaks": [{"bounds": ["sat", "mon"]}],
        },
        "yaxis": {  # Candlestick + indicadores de preço
            "title": "Preço",
            "domain": [0.3, 1],
            "autorange": True,
            "rangemode": "normal",
        },
        "yaxis2": {  # Volume
            "title": "Volume",
            "domain": [0.15, 0.3],
            "showgrid": False,
        },
        "yaxis3": {  # MACD
            "title": "MACD",
            "domain": [0, 0.15],
            "showgrid": False,
        },
        "hovermode": "x unified",
    }

    return {
        "data": plotly_data,
        "layout": layout,
    }


# ===========================================================================
# Gráfico 3 — Dispersão Risco × Distância (todos os ativos ranqueados)
# ===========================================================================


def build_scatter_chart_payload(
    ranking: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Monta o payload Plotly para o gráfico de dispersão Risco × Distância,
    colorido por setor, com linhas de quadrante.

    Fonte de dados: list[dict] retornada por build_ranking_result,
    que já contém os campos calculados por calculate_risk_return_indicators
    e enrich_with_metadata_and_52w_high.

    Campos consumidos por ativo
    ---------------------------
    - distancia    : distância percentual até o topo de 52 semanas (eixo X)
    - Risco_%      : risco percentual até o STOP ATR              (eixo Y)
    - sector       : setor de atuação (cor da série)
    - ticker       : rótulo de texto sobre o ponto
    - Retorno_Risco: relação retorno/risco (hover)

    Parâmetros
    ----------
    ranking : list[dict]
        Lista de ativos ranqueados, com os campos acima.

    Retorno
    -------
    dict com as chaves:
    - "data"   : list[dict] — traces Plotly (uma série por setor + linhas)
    - "layout" : dict       — configuração do layout Plotly
    """

    if not ranking:
        raise ValueError("ranking está vazio")

    df = pd.DataFrame(ranking)

    required_cols = ["distancia", "Risco_%", "ticker"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(
            f"Colunas obrigatórias ausentes no ranking: {missing}. "
            "Verifique se calculate_risk_return_indicators foi executado."
        )

    # Remove ativos sem os campos numéricos essenciais
    df = df.dropna(subset=["distancia", "Risco_%"])

    if df.empty:
        raise ValueError(
            "Nenhum ativo possui 'distancia' e 'Risco_%' válidos para o gráfico."
        )

    # Garante coluna de setor preenchida
    if "sector" not in df.columns:
        df["sector"] = "N/D"
    df["sector"] = df["sector"].fillna("N/D").astype(str)

    # Garante coluna de Retorno_Risco preenchida
    if "Retorno_Risco" not in df.columns:
        df["Retorno_Risco"] = np.nan
    df["Retorno_Risco"] = df["Retorno_Risco"].fillna(float("nan"))

    # ------------------------------------------------------------------
    # Pontos de corte dos quadrantes
    # ------------------------------------------------------------------
    x_min = float(df["distancia"].to_numpy(dtype=float).min())
    x_max = float(df["distancia"].to_numpy(dtype=float).max())
    y_min = float(df["Risco_%"].to_numpy(dtype=float).min())
    y_max = float(df["Risco_%"].to_numpy(dtype=float).max())

    mid_x = x_max / 2
    mid_y = y_max / 2

    # ------------------------------------------------------------------
    # Traces: uma série por setor (permite legenda interativa por cor)
    # ------------------------------------------------------------------
    plotly_data = []

    for sector in sorted(df["sector"].unique()):
        df_sector = df[df["sector"] == sector].copy()

        retorno_risco_values = [
            round(v, 2) if isinstance(v, float) and np.isfinite(v) else None
            for v in df_sector["Retorno_Risco"].tolist()
        ]

        plotly_data.append(
            {
                "type": "scatter",
                "mode": "markers+text",
                "name": sector,
                "x": df_sector["distancia"].tolist(),
                "y": df_sector["Risco_%"].tolist(),
                "text": df_sector["ticker"].tolist(),
                "textposition": "bottom right",
                "customdata": retorno_risco_values,
                "marker": {"size": 10},
                "hovertemplate": (
                    "<b>%{text}</b><br>"
                    "Distância: %{x:.2f}%<br>"
                    "Risco: %{y:.2f}%<br>"
                    "Retorno/Risco: %{customdata:.2f}"
                    "<extra>%{fullData.name}</extra>"
                ),
            }
        )

    # ------------------------------------------------------------------
    # Linha vertical — divide o eixo X no ponto médio
    # ------------------------------------------------------------------
    plotly_data.append(
        {
            "type": "scatter",
            "mode": "lines",
            "x": [mid_x, mid_x],
            "y": [y_min - 1, y_max + 1],
            "line": {"color": "red", "dash": "dash"},
            "showlegend": False,
            "hoverinfo": "skip",
        }
    )

    # ------------------------------------------------------------------
    # Linha horizontal — divide o eixo Y no ponto médio
    # ------------------------------------------------------------------
    plotly_data.append(
        {
            "type": "scatter",
            "mode": "lines",
            "x": [x_min - 1, x_max + 1],
            "y": [mid_y, mid_y],
            "line": {"color": "red", "dash": "dash"},
            "showlegend": False,
            "hoverinfo": "skip",
        }
    )

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    layout = {
        "title": "Dispersão por Setor — Risco × Distância do Topo (52 semanas)",
        "height": 500,
        "xaxis": {
            "title": "Distância até o Topo de 52 semanas (%)",
            "zeroline": False,
        },
        "yaxis": {
            "title": "Risco até o STOP ATR (%)",
            "zeroline": False,
        },
        "hovermode": "closest",
        "legend": {
            "title": {"text": "Setor"},
            "orientation": "v",
        },
    }

    return {
        "data": plotly_data,
        "layout": layout,
    }

```


**Tool Call: Check diagnostics for `C:\Users\Bruno\trend\app\charts\chart_builders.py`**
Status: Completed

File doesn't have errors or warnings!

## Assistant

Sem erros. Verificação geral:

**Tool Call: Check project diagnostics**
Status: Completed

C:\Users\Bruno\trend\app\data\market_data.py: 0 error(s), 1 warning(s)
C:\Users\Bruno\trend\app\data\market_data.py: 11 error(s), 0 warning(s)
C:\Users\Bruno\trend\app\services\ranking.py: 3 error(s), 0 warning(s)
C:\Users\Bruno\trend\app\data\preprocessing.py: 2 error(s), 2 warning(s)
C:\Users\Bruno\trend\app\data\preprocessing.py: 2 error(s), 0 warning(s)
C:\Users\Bruno\trend\app\core\ranking_pipeline.py: 2 error(s), 0 warning(s)
C:\Users\Bruno\trend\app\core\init.py: 0 error(s), 15 warning(s)
C:\Users\Bruno\trend\app\core\init.py: 2 error(s), 0 warning(s)


## Assistant

Todos os erros restantes são pré-existentes em `market_data.py`, `ranking.py`, `preprocessing.py`, `init.py` e `ranking_pipeline.py` (os dois deste último são os mesmos de antes — anotação de `DatetimeIndex` e indexação numpy). Nenhum arquivo novo ou modificado nesta tarefa introduziu erros.

---

## Resumo do que foi feito

### Identificação da fonte de dados

Todos os campos necessários para o gráfico já existiam no `result["ranking"]` produzido por `build_ranking_result`:

| Campo no gráfico | Origem no projeto |
|---|---|
| `distancia` | `calculate_risk_return_indicators` |
| `Risco_%` | `calculate_risk_return_indicators` |
| `Retorno_Risco` | `calculate_risk_return_indicators` |
| `sector` | `enrich_with_metadata_and_52w_high` |
| `ticker` | (era `Acao` no código antigo) |

### O que foi criado / modificado

| Arquivo | Alteração |
|---|---|
| `app/charts/chart_builders.py` | `build_scatter_chart_payload(ranking)` — traces por setor + linhas de quadrante |
| `app/api/routes.py` | Endpoint `GET /api/scatterchart` — leitura pura do `RankingRepository` |
| `ui/static/js/scatterchart.js` | Novo — ouve `fr:rankingReady`, chama `/api/scatterchart`, renderiza em `#scatterchart` |
| `ui/static/js/fr_chart.js` | Dispara `fr:rankingReady` após gráfico e tabela prontos |
| `ui/templates/index.html` | `<div id="scatterchart">` abaixo do candlestick + `<script>` do `scatterchart.js` |

### Fluxo

```/dev/null/flow.txt#L1-8
runPipeline()
  └── /api/fr-price-series  →  gráfico FR + tabela (sem recomputação)
          │
          └── dispara fr:rankingReady
                  │
                  └── scatterchart.js  →  GET /api/scatterchart
                          │                (lê ranking_repository — zero cálculo)
                          └── Plotly renderiza dispersão em #scatterchart
```

