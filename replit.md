# Dash Finance - Trend Following B3

## Overview
A Python Dash web application for analyzing Brazilian stock market (B3) trends. It downloads financial data, calculates weighted momentum factors, and displays interactive charts with technical indicators (Bollinger Bands, MACD, ATR Stop Loss).

## Architecture
- **Language**: Python 3.10
- **Framework**: Dash (Flask-based) with Bootstrap components
- **Key Libraries**: yfinance, TA-Lib, pandas, plotly, dash-bootstrap-components
- **System Dependency**: ta-lib C library (installed via Nix)
- **Port**: 5000 (development and production)

## Project Structure
- `main.py` - Main application file (converted from Jupyter notebook)
- `requirements.txt` - Python dependencies
- `Dockerfile` - Original Docker setup (not used in Replit)

## How It Works
1. User selects a reference date and clicks "Executar"
2. App fetches stock data from brapi.dev API and yfinance
3. Calculates a weighted momentum factor (FR) for each stock
4. Filters stocks with FR >= 80
5. Displays interactive candlestick charts with technical indicators

## Deployment
- Development: `python main.py` on port 5000
- Production: `gunicorn --bind=0.0.0.0:5000 --reuse-port main:server`
