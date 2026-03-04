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
