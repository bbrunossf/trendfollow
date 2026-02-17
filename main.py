from fastapi import FastAPI, Query
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

from app.core import config
from app.core.pipeline import run_pipeline

# =========================================================
# FastAPI app
# =========================================================

app = FastAPI(
    title="Trend Following API",
    description="API para análise de força relativa e ranking de ativos da B3",
    version="0.1.0",
)

# =========================================================
# Models (temporariamente aqui; depois vão para models.py)
# =========================================================


class AnalysisRequest(BaseModel):
    reference_date: Optional[date] = Field(
        default=None, description="Data de referência para a análise")

    analysis_months: int = Field(default=config.ANALYSIS_MONTHS,
                                 ge=1,
                                 description="Horizonte de análise em meses")

    min_price: float = Field(default=config.MIN_PRICE,
                             ge=0,
                             description="Preço mínimo do ativo")

    min_volume: int = Field(default=config.MIN_VOLUME,
                            ge=0,
                            description="Volume mínimo negociado")

    fr_min_threshold: float = Field(default=config.FR_MIN_THRESHOLD,
                                    ge=0,
                                    le=100,
                                    description="Força relativa mínima")

    top_n: Optional[int] = Field(
        default=config.TOP_N_ASSETS,
        ge=1,
        description="Quantidade máxima de ativos no ranking")


# =========================================================
# Endpoints
# =========================================================


@app.get("/health")
def health_check():
    """
    Endpoint simples para verificação de status.
    """
    return {"status": "ok"}


@app.get("/run")
def run_trend_following(reference_date: Optional[str] = Query(
    default=None, description="Data de referência no formato YYYY-MM-DD")):
    """
    Executa o pipeline completo e retorna ranking e summary.
    """

    result = run_pipeline(reference_date=reference_date)

    return {
        "summary": result["summary"],
        "ranking": result["ranking"],
        "metadata": result.get("metadata", {}),
        "charts": result.get("charts", {})
    }
