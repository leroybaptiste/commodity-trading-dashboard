import numpy as np
import pandas as pd
from scipy.stats import norm


# ============================================================
# BLACK-76 OPTION PRICING FUNCTIONS
# ============================================================

def black_76_price(
    futures_price,
    strike_price,
    time_to_maturity,
    risk_free_rate,
    volatility,
    option_type
):
    """
    Price a European option on a futures contract using the Black-76 model.

    futures_price : current futures price
    strike_price : option strike
    time_to_maturity : time to maturity in years
    risk_free_rate : annual risk-free rate
    volatility : annualized volatility
    option_type : "Call" or "Put"
    """

    if time_to_maturity <= 0 or volatility <= 0:
        return max(futures_price - strike_price, 0) if option_type == "Call" else max(strike_price - futures_price, 0)

    d1 = (
        np.log(futures_price / strike_price)
        + 0.5 * volatility ** 2 * time_to_maturity
    ) / (volatility * np.sqrt(time_to_maturity))

    d2 = d1 - volatility * np.sqrt(time_to_maturity)

    discount_factor = np.exp(-risk_free_rate * time_to_maturity)

    if option_type == "Call":
        price = discount_factor * (
            futures_price * norm.cdf(d1)
            - strike_price * norm.cdf(d2)
        )
    else:
        price = discount_factor * (
            strike_price * norm.cdf(-d2)
            - futures_price * norm.cdf(-d1)
        )

    return price


def black_76_greeks(
    futures_price,
    strike_price,
    time_to_maturity,
    risk_free_rate,
    volatility,
    option_type
):
    """
    Compute main Black-76 Greeks.

    Delta, Gamma, Vega and Theta are calculated for an option on futures.
    """

    if time_to_maturity <= 0 or volatility <= 0:
        return {
            "Delta": np.nan,
            "Gamma": np.nan,
            "Vega": np.nan,
            "Theta": np.nan
        }

    d1 = (
        np.log(futures_price / strike_price)
        + 0.5 * volatility ** 2 * time_to_maturity
    ) / (volatility * np.sqrt(time_to_maturity))

    d2 = d1 - volatility * np.sqrt(time_to_maturity)

    discount_factor = np.exp(-risk_free_rate * time_to_maturity)

    if option_type == "Call":
        delta = discount_factor * norm.cdf(d1)
        theta = (
            -discount_factor * futures_price * norm.pdf(d1) * volatility / (2 * np.sqrt(time_to_maturity))
            + risk_free_rate * discount_factor * (
                futures_price * norm.cdf(d1) - strike_price * norm.cdf(d2)
            )
        )
    else:
        delta = -discount_factor * norm.cdf(-d1)
        theta = (
            -discount_factor * futures_price * norm.pdf(d1) * volatility / (2 * np.sqrt(time_to_maturity))
            + risk_free_rate * discount_factor * (
                strike_price * norm.cdf(-d2) - futures_price * norm.cdf(-d1)
            )
        )

    gamma = discount_factor * norm.pdf(d1) / (
        futures_price * volatility * np.sqrt(time_to_maturity)
    )

    vega = discount_factor * futures_price * norm.pdf(d1) * np.sqrt(time_to_maturity)

    return {
        "Delta": delta,
        "Gamma": gamma,
        "Vega": vega,
        "Theta": theta
    }


def create_option_payoff_table(
    futures_price,
    strike_price,
    option_premium,
    option_type
):
    """
    Create a payoff table for different futures price scenarios at maturity.
    """

    price_scenarios = np.linspace(
        futures_price * 0.6,
        futures_price * 1.4,
        25
    )

    rows = []

    for price in price_scenarios:
        if option_type == "Call":
            payoff = max(price - strike_price, 0)
        else:
            payoff = max(strike_price - price, 0)

        pnl = payoff - option_premium

        rows.append({
            "Futures Price at Maturity": price,
            "Option Payoff": payoff,
            "Option Premium": option_premium,
            "Net P&L": pnl
        })

    return pd.DataFrame(rows)


def create_volatility_sensitivity_table(
    futures_price,
    strike_price,
    time_to_maturity,
    risk_free_rate,
    option_type,
    volatility_range
):
    """
    Create a sensitivity table showing how the option price changes
    when implied volatility changes.
    """

    rows = []

    for vol in volatility_range:
        price = black_76_price(
            futures_price=futures_price,
            strike_price=strike_price,
            time_to_maturity=time_to_maturity,
            risk_free_rate=risk_free_rate,
            volatility=vol,
            option_type=option_type
        )

        rows.append({
            "Volatility": vol,
            "Option Price": price
        })

    return pd.DataFrame(rows)
