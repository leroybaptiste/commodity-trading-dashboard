# Commodity Trading & Hedging Dashboard

## Live Dashboard

The interactive dashboard is available here:

https://commodity-hedging-dashboard.streamlit.app

## Project Overview

This project is an interactive commodity finance dashboard built with Python and Streamlit.

The objective is to develop a practical tool combining market monitoring, futures curve analysis, hedging simulation, risk management, trade finance and options pricing.

The project is designed to demonstrate a strong interest in commodity markets and the ability to build practical analytical tools for commodity trading, hedging and financing use cases.

## Current Features

### 1. Market Overview

The Market Overview module provides a snapshot of major commodity markets.

It includes:

- Historical price charts
- Daily returns
- Moving averages
- Multi-commodity market snapshot
- Performance analysis
- Annualized volatility
- Maximum drawdown
- Historical VaR 95%
- Cross-commodity correlation matrix
- Excel export

Covered commodities include:

- WTI Crude Oil
- Brent Crude Oil
- Natural Gas
- Gold
- Copper
- Wheat
- Corn

### 2. Futures Curve Analysis

The Futures Curve Analysis module simulates and analyses commodity futures curves.

It includes:

- Contango scenarios
- Backwardation scenarios
- Flat curve scenarios
- Futures prices by maturity
- M1, M2, M3, M6 and M12 contracts
- Spread analysis
- Roll yield approximation
- Automatic interpretation of the curve structure

This module is useful to understand how futures markets reflect storage costs, supply-demand tensions and market expectations.

### 3. Hedging Simulator

The Hedging Simulator module allows users to simulate the hedging of a physical commodity exposure using futures contracts.

It includes:

- Buyer / consumer hedge
- Producer / seller hedge
- Physical exposure
- Futures position
- Contract size
- Hedge ratio
- Number of futures contracts
- Physical P&L
- Futures P&L
- Net hedged P&L
- Basis risk
- Scenario analysis
- Excel export

This module demonstrates how futures contracts can be used to reduce price risk on physical commodity exposures.

### 4. Risk Management

The Risk Management module measures the risk of a commodity position using historical market data.

It includes:

- Position value
- Long / short exposure
- Historical daily P&L
- Daily and annualized volatility
- VaR 95%
- VaR 99%
- Expected Shortfall 95%
- Expected Shortfall 99%
- Worst daily loss
- Best daily gain
- Cumulative P&L
- Drawdown analysis
- Stress testing
- Excel export

This module is designed to replicate basic market risk metrics used in trading, risk management and commodity finance.

### 5. Trade Finance / Borrowing Base

The Trade Finance module simulates the financing of a physical commodity inventory.

It includes:

- Inventory quantity
- Market price
- Inventory value
- Haircut
- Eligible collateral value
- Advance rate
- Borrowing base
- Loan amount
- Available liquidity
- Loan-to-value
- Coverage ratio
- Margin call detection
- Price stress tests

This module connects commodity markets with structured commodity finance and borrowing base facilities.

It shows how a bank or lender can determine the amount of financing available against a physical commodity inventory.

### 6. Commodity Options Pricer

The Options Pricer module prices European options on commodity futures using the Black-76 model.

It includes:

- Call and put options
- Futures price
- Strike price
- Time to maturity
- Risk-free rate
- Implied volatility
- Option premium
- Delta
- Gamma
- Vega
- Theta
- Payoff at maturity
- Volatility sensitivity analysis
- Automatic interpretation

The Black-76 model is relevant for commodity markets because many listed commodity options are written on futures contracts rather than directly on spot prices.

## Financial Concepts Covered

This project covers several key concepts used in commodity trading and commodity finance:

- Spot prices
- Futures prices
- Futures curves
- Contango
- Backwardation
- Roll yield
- Basis risk
- Physical exposure
- Futures hedging
- Buyer hedge
- Producer hedge
- Market risk
- Historical volatility
- Value at Risk
- Expected Shortfall
- Drawdown
- Stress testing
- Inventory financing
- Borrowing base
- Haircut
- Advance rate
- Loan-to-value
- Margin call
- Options on futures
- Black-76 pricing model
- Greeks

## Technologies Used

- Python
- Streamlit
- pandas
- numpy
- yfinance
- plotly
- scipy
- openpyxl
- xlsxwriter
- Git
- GitHub

## Project Structure

```text
commodity-trading-dashboard/

├── app.py
├── README.md
├── requirements.txt
├── .gitignore
│
└── src/
    ├── __init__.py
    ├── market_utils.py
    ├── excel_export.py
    ├── trade_finance.py
    └── options_pricer.py