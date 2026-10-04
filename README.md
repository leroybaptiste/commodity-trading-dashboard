# Commodity Trading & Hedging Dashboard

Interactive Python dashboard for commodity market analysis, futures curve interpretation, hedging simulation and risk management.

Live application: https://commodity-hedging-dashboard.streamlit.app

## Project Overview

This project is designed as a practical commodity trading and risk management tool.

It focuses on four core areas:

- Market overview
- Futures curve analysis
- Physical exposure hedging
- Market risk management

The dashboard uses historical market data to analyze commodity prices, returns, volatility, correlations, futures curve structures, hedge effectiveness and risk indicators.

## Modules

### 1. Market Overview

This module provides a multi-commodity market snapshot.

It includes:

- Latest price
- Period performance
- Annualized volatility
- Maximum drawdown
- Historical VaR 95%
- Cross-commodity correlation matrix
- Historical price chart
- Daily returns chart
- Excel export

### 2. Futures Curve Analysis

This module simulates simplified commodity futures curves.

It allows the user to analyze:

- Contango
- Backwardation
- Flat curve structures
- M12-M1 spreads
- Curve slope
- Approximate roll yield
- Spread analysis by maturity

### 3. Hedging Simulator

This module simulates a futures hedge for a physical commodity exposure.

It compares:

- Physical exposure P&L
- Futures position P&L
- Net P&L after hedging
- Effective price after hedge
- Target hedge ratio versus actual hedge ratio
- Scenario analysis under different price shocks

### 4. Risk Management

This module measures the market risk of a commodity position.

It includes:

- Daily volatility
- Annualized volatility
- Value-at-Risk 95%
- Value-at-Risk 99%
- Expected Shortfall
- Historical P&L distribution
- Cumulative P&L
- Historical drawdown
- Stress tests
- Excel export

## Technologies Used

- Python
- Streamlit
- pandas
- numpy
- Plotly
- yfinance
- openpyxl
- xlsxwriter

## Data Source

Market data is retrieved from Yahoo Finance through the `yfinance` Python library.

The calculations are based on historical daily closing prices.

## Purpose

The objective of this project is to demonstrate practical skills in:

- Commodity market analysis
- Futures curve interpretation
- Hedging mechanics
- Risk management
- Python dashboard development
- Financial data visualization
- Excel report generation

## How to Run Locally

Clone the repository:

```bash
git clone https://github.com/leroybaptiste/commodity-trading-dashboard.git
cd commodity-trading-dashboard