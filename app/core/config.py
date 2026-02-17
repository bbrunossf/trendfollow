"""
config.py

Parâmetros globais de configuração do sistema.
Contém apenas constantes e valores default.
"""

# ===============================
# Universo de ativos (BRAPI)
# ===============================
MIN_PRICE = 5.0
MIN_VOLUME = 1_000_000
EXCLUDED_TICKER_SUFFIXES = ("11", "32")

# ===============================
# Horizonte temporal
# ===============================
ANALYSIS_MONTHS = 6
DATE_FORMAT = "%Y-%m-%d"

# ===============================
# Indicadores técnicos
# ===============================
MA_WINDOW = 20

BOLLINGER_WINDOW = 20
BOLLINGER_STD = 2

MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

ATR_WINDOW = 14
ATR_MULTIPLIER = 1.5

# ===============================
# Scoring e Ranking
# ===============================
FR_SCALE = (0, 100)
FR_MIN_THRESHOLD = 80.0
TOP_N_ASSETS = None

# ===============================
# Infraestrutura
# ===============================
REQUEST_TIMEOUT = 30
ENABLE_CACHE = False
