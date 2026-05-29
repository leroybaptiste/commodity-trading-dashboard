# Commodity Trading & Hedging Dashboard

## Project Overview

This project is a Python-based dashboard designed to monitor commodity markets, analyze futures curves, simulate hedging strategies and measure market risk.

The goal is to build a practical tool inspired by real use cases in commodity trading, hedging and risk management.

The dashboard is built with Streamlit and uses historical market data to provide interactive analysis across several commodity markets.

## Current Features

### 1. Market Overview

The Market Overview module allows users to monitor several commodities, including:

- WTI Crude Oil
- Brent Crude Oil
- Natural Gas
- Gold
- Copper
- Wheat
- Corn

The module includes:

- Historical price chart
- Daily returns
- Moving averages
- Multi-commodity snapshot
- Period performance
- Annualized volatility
- Maximum drawdown
- Historical VaR
- Cross-commodity correlation matrix

### 2. Futures Curve Analysis

The Futures Curve module allows users to build and analyze a simplified commodity futures curve.

The module includes:

- Manual input of futures prices by maturity
- Contango / backwardation detection
- Spread analysis versus front-month contract
- Curve slope calculation
- Approximate roll yield
- Automatic interpretation of the curve structure

### 3. Hedging Simulator

The Hedging Simulator allows users to simulate a futures hedge on a physical commodity exposure.

The module includes:

- Buyer hedge simulation
- Producer hedge simulation
- Long futures and short futures positions
- Exact number of contracts
- Rounded number of contracts
- Actual hedge ratio after rounding
- Physical P&L
- Futures P&L
- Net hedged P&L
- Effective hedged price
- Scenario analysis
- Basis risk illustration

### 4. Risk Management

The Risk Management module measures the market risk of a commodity position using historical returns.

The module includes:

- Daily volatility
- Annualized volatility
- Historical VaR 95%
- Historical VaR 99%
- Expected Shortfall 95%
- Expected Shortfall 99%
- Historical P&L distribution
- Cumulative P&L
- Drawdown chart
- Stress tests
- Automatic risk interpretation

## Technologies Used

- Python
- Streamlit
- pandas
- numpy
- yfinance
- plotly
- Excel
- VBA

## Financial Concepts Covered

This project applies several financial and commodity market concepts:

- Spot price
- Futures price
- Contango
- Backwardation
- Roll yield
- Basis risk
- Hedging
- Buyer hedge
- Producer hedge
- Futures P&L
- Value-at-Risk
- Expected Shortfall
- Volatility
- Drawdown
- Stress testing
- Correlation analysis

## How to Run the Project

Clone the repository:

```bash
git clone https://github.com/leroybaptiste/commodity-trading-dashboard.git