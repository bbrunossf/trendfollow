# Dash Finance - Trend Following B3

## Overview
A FastAPI web application for analyzing Brazilian stock market (B3) trends using a Trend Following strategy. It identifies stocks with strong relative strength and upward momentum over the last 6 months.

## Architecture
- **Language**: Python 3.10
- **Framework**: FastAPI with Jinja2 templates
- **Frontend**: Vanilla JavaScript + Plotly.js for interactive charts
- **Key Libraries**: fastapi, uvicorn, yfinance, brapi, pandas, numpy, plotly, jinja2
- **Port**: 5000

## Project Structure
- `main.py` - FastAPI app entry point; mounts static files and Jinja2 templates
- `app/api/routes.py` - API endpoints (ranking, candlestick chart, scatter chart)
- `app/core/` - Orchestration: ranking pipeline and initialization
- `app/data/` - Data acquisition via BRAPI and yfinance; preprocessing
- `app/finance/` - Financial indicators (Bollinger, MACD, ATR, returns, volatility)
- `app/services/` - Scoring and ranking business logic (Força Relativa)
- `app/charts/` - Plotly JSON payload builders
- `app/config.py` - Global settings (MIN_PRICE, MIN_VOLUME, indicator params)
- `ui/templates/` - HTML Jinja2 templates
- `ui/static/` - CSS and JavaScript assets
- `requirements.txt` - Python dependencies
- `Dockerfile` - Original Docker setup (not used in Replit)

## How It Works
1. App fetches all B3 tickers via BRAPI and filters by volume and price
2. Downloads historical OHLCV data via yfinance
3. Calculates technical indicators (SMA, Bollinger Bands, MACD, ATR)
4. Computes Força Relativa (Relative Strength) by comparing 6-month price snapshots
5. Ranks assets and selects those in the top 80th percentile
6. Serves an interactive dashboard with ranking table and drill-down charts

## Running
- **Workflow command**: `uvicorn main:app --host 0.0.0.0 --port 5000`
