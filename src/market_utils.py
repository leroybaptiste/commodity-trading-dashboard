import pandas as pd
import numpy as np
import yfinance as yf
import streamlit as st


# ============================================================
# DICTIONNAIRE DES COMMODITIES
# ============================================================

# Chaque commodity est associée à son ticker Yahoo Finance.
# Exemple : CL=F correspond au contrat futures WTI Crude Oil.
COMMODITY_TICKERS = {
    "WTI Crude Oil": "CL=F",
    "Brent Crude Oil": "BZ=F",
    "Natural Gas": "NG=F",
    "Gold": "GC=F",
    "Copper": "HG=F",
    "Wheat": "ZW=F",
    "Corn": "ZC=F"
}

# ============================================================
# FONCTION DE CHARGEMENT DES DONNÉES
# ============================================================

@st.cache_data(ttl=3600)
def load_price_data(ticker, period):
    """
    Télécharge les prix historiques d'une commodity depuis Yahoo Finance.

    ticker : code Yahoo Finance, par exemple CL=F pour le WTI.
    period : période choisie, par exemple 1y pour 1 an.
    """

    data = yf.download(
        ticker,
        period=period,
        interval="1d",
        auto_adjust=True,
        progress=False
    )

    if data.empty:
        return pd.Series(dtype=float)

    try:
        close_prices = data["Close"]
    except KeyError:
        return pd.Series(dtype=float)

    if isinstance(close_prices, pd.DataFrame):
        close_prices = close_prices.iloc[:, 0]

    close_prices = close_prices.dropna()
    close_prices.name = "Price"

    return close_prices

# ============================================================
# FONCTION DE CALCUL DES MÉTRIQUES DE MARCHÉ
# ============================================================

def compute_market_metrics(price_series):
    """
    Calcule les principaux indicateurs de marché à partir d'une série de prix.
    """

    returns = price_series.pct_change().dropna()

    last_price = price_series.iloc[-1]
    first_price = price_series.iloc[0]

    period_performance = last_price / first_price - 1

    if len(price_series) > 1:
        daily_performance = last_price / price_series.iloc[-2] - 1
    else:
        daily_performance = np.nan

    annualized_volatility = returns.std() * np.sqrt(252)

    running_max = price_series.cummax()
    drawdowns = price_series / running_max - 1
    max_drawdown = drawdowns.min()

    var_95 = returns.quantile(0.05)

    return {
        "last_price": last_price,
        "daily_performance": daily_performance,
        "period_performance": period_performance,
        "annualized_volatility": annualized_volatility,
        "max_drawdown": max_drawdown,
        "var_95": var_95,
        "returns": returns,
        "drawdowns": drawdowns
    }

# ============================================================
# FONCTIONS DE FORMATAGE
# ============================================================

def format_percentage(value):
    """
    Transforme un nombre décimal en pourcentage lisible.
    Exemple : 0.125 devient 12.50%.
    """

    if pd.isna(value):
        return "N/A"
    return f"{value:.2%}"


def format_number(value):
    """
    Affiche un nombre avec deux décimales.
    """

    if pd.isna(value):
        return "N/A"
    return f"{value:,.2f}"
