
# Commodity Trading & Hedging Dashboard

# Streamlit sert à créer l'application web interactive.
import streamlit as st

# pandas sert à manipuler les tableaux de données.
import pandas as pd

# numpy sert aux calculs mathématiques.
import numpy as np

# plotly sert à créer des graphiques interactifs.
import plotly.graph_objects as go
import plotly.express as px

from src.market_utils import (
    COMMODITY_TICKERS,
    load_price_data,
    compute_market_metrics,
    format_percentage,
    format_number
)

from src.excel_export import (
    create_market_excel_report,
    create_hedging_excel_report,
    create_risk_excel_report
)

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Commodity Trading & Hedging Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# MAIN HEADER
# ============================================================

st.title("Commodity Trading & Hedging Dashboard")

st.markdown("""
Interactive Python dashboard for commodity markets, hedging, risk management, trade finance and options pricing.
""")

st.markdown("""
This project combines market data analysis, futures curve interpretation, physical exposure hedging
and historical risk metrics in a single practical tool.
""")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Modules", "4")

with col2:
    st.metric("Asset class", "Commodities")

with col3:
    st.metric("Focus", "Trading & Finance")

st.divider()

# ============================================================
# SIDEBAR SETTINGS
# ============================================================

st.sidebar.header("Dashboard Settings")

st.sidebar.markdown("""
Select a commodity and a historical period.

These inputs are used across the market overview, futures curve,
hedging and risk management modules.
""")

selected_commodity = st.sidebar.selectbox(
    "Commodity",
    list(COMMODITY_TICKERS.keys())
)

selected_period = st.sidebar.selectbox(
    "Historical period",
    ["1mo", "3mo", "6mo", "1y", "3y", "5y"],
    index=3
)

ticker = COMMODITY_TICKERS[selected_commodity]

st.sidebar.divider()

st.sidebar.subheader("Selected Market")

st.sidebar.markdown(f"""
**Commodity**  
{selected_commodity}

**Yahoo Finance ticker**  
{ticker}
""")

st.sidebar.divider()

st.sidebar.subheader("Project Scope")

st.sidebar.markdown("""
- Market monitoring
- Futures curve analysis
- Physical exposure hedging
- Market risk metrics
""")

st.sidebar.divider()

st.sidebar.caption("""
Data source: Yahoo Finance via yfinance.  
Calculations are based on historical daily closing prices.
""")

# ============================================================
# CHARGEMENT DES DONNÉES
# ============================================================

price_series = load_price_data(ticker, selected_period)

if price_series.empty:
    st.error("Aucune donnée disponible pour cette commodity. Essaie une autre commodity ou une autre période.")
    st.stop()

metrics = compute_market_metrics(price_series)

# ============================================================
# TABS PRINCIPAUX
# ============================================================

tab1, tab2, tab3, tab4 = st.tabs([
    "Market Overview",
    "Futures Curve",
    "Hedging Simulator",
    "Risk Management"
])

# ============================================================
# TAB 1 - MARKET OVERVIEW
# ============================================================

with tab1:
    st.header("Market Overview")


    # ========================================================
    # MULTI-COMMODITY MARKET SNAPSHOT
    # ========================================================

    st.subheader("Multi-Commodity Market Snapshot")

    st.markdown("""
    This table provides a quick comparison of the main commodities covered by the dashboard.
It summarizes the latest price, period performance, volatility, maximum drawdown and historical VaR.
    """)

    snapshot_rows = []

    # On boucle sur toutes les commodities du dictionnaire.
    # Pour chaque commodity, on télécharge les prix et on calcule les métriques.
    for commodity_name, commodity_ticker in COMMODITY_TICKERS.items():

        commodity_prices = load_price_data(commodity_ticker, selected_period)

        # Si les données sont vides, on ignore la commodity.
        if commodity_prices.empty:
            continue

        commodity_metrics = compute_market_metrics(commodity_prices)

        snapshot_rows.append({
            "Commodity": commodity_name,
            "Last Price": commodity_metrics["last_price"],
            "Period Performance": commodity_metrics["period_performance"],
            "Annualized Volatility": commodity_metrics["annualized_volatility"],
            "Max Drawdown": commodity_metrics["max_drawdown"],
            "Historical VaR 95%": commodity_metrics["var_95"]
        })

    snapshot_df = pd.DataFrame(snapshot_rows)

    # On crée une copie formatée pour l'affichage.
    # L'idée est de garder snapshot_df en format numérique pour les calculs,
    # et d'utiliser snapshot_display pour un affichage propre dans Streamlit.
    snapshot_display = snapshot_df.copy()

    snapshot_display["Last Price"] = snapshot_display["Last Price"].apply(lambda x: f"{x:,.2f}")
    snapshot_display["Period Performance"] = snapshot_display["Period Performance"].apply(lambda x: f"{x:.2%}")
    snapshot_display["Annualized Volatility"] = snapshot_display["Annualized Volatility"].apply(lambda x: f"{x:.2%}")
    snapshot_display["Max Drawdown"] = snapshot_display["Max Drawdown"].apply(lambda x: f"{x:.2%}")
    snapshot_display["Historical VaR 95%"] = snapshot_display["Historical VaR 95%"].apply(lambda x: f"{x:.2%}")

    st.dataframe(snapshot_display, width="stretch")

    # ========================================================
    # CROSS-COMMODITY CORRELATION MATRIX
    # ========================================================

    st.subheader("Cross-Commodity Correlation Matrix")

    st.markdown("""
    This matrix measures the correlation between daily returns across the selected commodities.

A correlation close to **1** means that two commodities tend to move in the same direction.  
A correlation close to **0** means that there is little linear relationship.  
A negative correlation means that they tend to move in opposite directions.
    """)

    all_returns = {}

    # On récupère les rendements journaliers pour chaque commodity.
    for commodity_name, commodity_ticker in COMMODITY_TICKERS.items():

        commodity_prices = load_price_data(commodity_ticker, selected_period)

        if commodity_prices.empty:
            continue

        # Rendement journalier :
        # Return_t = Price_t / Price_t-1 - 1
        commodity_returns = commodity_prices.pct_change().dropna()

        all_returns[commodity_name] = commodity_returns

    # On rassemble tous les rendements dans un seul DataFrame.
    # Chaque colonne correspond à une commodity.
    returns_matrix = pd.DataFrame(all_returns)

    # On supprime les dates où certaines commodities n'ont pas de données.
    returns_matrix = returns_matrix.dropna()

    # On initialise une matrice vide.
    # Cela évite une erreur si les données sont insuffisantes.
    correlation_matrix = pd.DataFrame()

    if returns_matrix.empty:
        st.warning("Not enough data to compute the correlation matrix.")
    else:
        # La corrélation est calculée sur les rendements, pas sur les prix.
        # C'est important car on veut comparer les variations, pas les niveaux de prix.
        correlation_matrix = returns_matrix.corr()

        fig_corr = px.imshow(
            correlation_matrix,
            text_auto=".2f",
            title="Correlation Matrix - Daily Returns",
            aspect="auto"
        )

        fig_corr.update_layout(
            height=600
        )

        st.plotly_chart(fig_corr, width="stretch")

        st.markdown("""
        **Quick interpretation:**

- A high correlation between two commodities may indicate exposure to common market drivers.
- A low correlation can be useful from a diversification perspective.
- This analysis helps identify cross-market risk across commodity markets.
        """)
    # ========================================================
    # EXCEL EXPORT - MARKET OVERVIEW
    # ========================================================

    st.subheader("Export Excel")

    st.markdown("""
    This button downloads an Excel file containing the market snapshot,
the correlation matrix and key report metadata.
    """)

    excel_report = create_market_excel_report(
        snapshot_df=snapshot_df,
        correlation_matrix=correlation_matrix,
        selected_commodity=selected_commodity,
        selected_period=selected_period
    )

    clean_commodity_name = selected_commodity.lower().replace(" ", "_").replace("/", "_")

    st.download_button(
        label="Télécharger le rapport Excel",
        data=excel_report,
        file_name=f"market_overview_{clean_commodity_name}_{selected_period}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.markdown("---")

    st.markdown("---")

    st.markdown("""
    This section displays the historical prices of the selected commodity
    and computes the main market indicators.
    """)

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric(
        "Last Price",
        format_number(metrics["last_price"])
    )

    col2.metric(
        "1-day performance",
        format_percentage(metrics["daily_performance"])
    )

    col3.metric(
        "Period performance",
        format_percentage(metrics["period_performance"])
    )

    col4.metric(
        "Annualized volatility",
        format_percentage(metrics["annualized_volatility"])
    )

    col5.metric(
        "Max Drawdown",
        format_percentage(metrics["max_drawdown"])
    )

    # Création d'un DataFrame pour le graphique.
    chart_data = pd.DataFrame({
        "Price": price_series,
        "Moving Average 20D": price_series.rolling(window=20).mean(),
        "Moving Average 50D": price_series.rolling(window=50).mean()
    })

    # Graphique des prix avec moyennes mobiles.
    fig_price = go.Figure()

    fig_price.add_trace(go.Scatter(
        x=chart_data.index,
        y=chart_data["Price"],
        mode="lines",
        name="Price"
    ))

    fig_price.add_trace(go.Scatter(
        x=chart_data.index,
        y=chart_data["Moving Average 20D"],
        mode="lines",
        name="MA 20D"
    ))

    fig_price.add_trace(go.Scatter(
        x=chart_data.index,
        y=chart_data["Moving Average 50D"],
        mode="lines",
        name="MA 50D"
    ))

    fig_price.update_layout(
        title=f"{selected_commodity} - Historical Price",
        xaxis_title="Date",
        yaxis_title="Price",
        height=500
    )

    st.plotly_chart(fig_price, width="stretch")

    # Graphique des rendements journaliers.
    returns_df = metrics["returns"].to_frame(name="Daily Returns")

    fig_returns = px.line(
        returns_df,
        y="Daily Returns",
        title=f"{selected_commodity} - Daily Returns"
    )

    fig_returns.update_layout(
        xaxis_title="Date",
        yaxis_title="Daily Returns",
        height=400
    )

    st.plotly_chart(fig_returns, width="stretch")


# ============================================================
# TAB 2 - FUTURES CURVE ANALYSIS
# ============================================================

with tab2:
    st.header("Futures Curve Analysis")

    st.markdown("""
    This section analyzes a simplified futures curve.

    In commodity trading, the shape of the futures curve is important:
    - a **contango** curve means that longer-dated futures prices are higher than short-dated prices;
    - a **backwardation** curve means that longer-dated futures prices are lower than short-dated prices;
    - the curve structure influences roll yield, carrying costs and trading strategies.
    """)

    st.subheader("1. Curve Parameters")

    # On utilise le dernier prix observé comme base de départ.
    # Cela permet d'avoir des valeurs cohérentes avec la commodity sélectionnée.
    base_price = float(metrics["last_price"])

    col1, col2 = st.columns(2)

    with col1:
        curve_scenario = st.selectbox(
            "Curve scenario",
            ["Contango", "Backwardation", "Flat"]
        )

    with col2:
        curve_intensity = st.slider(
            "Curve slope intensity",
            min_value=0.0,
            max_value=0.20,
            value=0.05,
            step=0.01
        )

    # Liste des maturités utilisées.
    maturities = ["M1", "M2", "M3", "M6", "M12"]

    # Coefficients approximatifs pour représenter l'éloignement des maturités.
    # M1 est la première maturité, M12 la maturité la plus longue.
    maturity_factors = np.array([0.00, 0.20, 0.35, 0.60, 1.00])

    # Construction automatique d'une courbe par défaut selon le scénario choisi.
    if curve_scenario == "Contango":
        default_curve_prices = base_price * (1 + curve_intensity * maturity_factors)
    elif curve_scenario == "Backwardation":
        default_curve_prices = base_price * (1 - curve_intensity * maturity_factors)
    else:
        default_curve_prices = base_price * np.ones(len(maturities))

    st.subheader("2. Futures Prices by Maturity")

    st.markdown("""
    The futures prices below can be manually adjusted.  
    This allows users to test different futures curve shapes.
    """)

    curve_prices = []

    cols = st.columns(len(maturities))

    for i, maturity in enumerate(maturities):
        price = cols[i].number_input(
            f"{maturity} price",
            min_value=0.0,
            value=float(default_curve_prices[i]),
            step=0.1
        )
        curve_prices.append(price)

    # Création du DataFrame de courbe.
    curve_df = pd.DataFrame({
        "Maturity": maturities,
        "Futures Price": curve_prices
    })

    # Prix de la première maturité.
    front_price = curve_prices[0]

    # Prix de la maturité la plus longue.
    long_price = curve_prices[-1]

    # Spread entre M12 et M1.
    spread_m12_m1 = long_price - front_price

    # Pente relative de la courbe.
    # Formule : Slope = M12 / M1 - 1
    curve_slope = long_price / front_price - 1

    # Roll yield approximatif pour une position long.
    # Si la courbe est en contango, le roll yield long est généralement négatif.
    # Si la courbe est en backwardation, le roll yield long est généralement positif.
    roll_yield_approx = (front_price - long_price) / front_price

    # Détection automatique de la structure.
    if spread_m12_m1 > 0:
        detected_structure = "Contango"
    elif spread_m12_m1 < 0:
        detected_structure = "Backwardation"
    else:
        detected_structure = "Flat"

    st.subheader("3. Futures Curve Structure Indicators")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Detected structure", detected_structure)
    col2.metric("Spread M12 - M1", format_number(spread_m12_m1))
    col3.metric("M12 / M1 slope", format_percentage(curve_slope))
    col4.metric("Roll yield approx.", format_percentage(roll_yield_approx))

    # Graphique de la courbe futures.
    fig_curve = px.line(
        curve_df,
        x="Maturity",
        y="Futures Price",
        markers=True,
        title=f"{selected_commodity} - Futures Curve"
    )

    fig_curve.update_layout(
        xaxis_title="Maturity",
        yaxis_title="Futures price",
        height=500
    )

    st.plotly_chart(fig_curve, width="stretch")

    st.subheader("4. Spread Analysis")

    # On calcule les spreads de chaque maturité par rapport à M1.
    # Exemple : Spread M6-M1 = Prix M6 - Prix M1
    spread_rows = []

    for maturity, price in zip(maturities, curve_prices):
        spread = price - front_price
        spread_percentage = spread / front_price

        spread_rows.append({
            "Maturity": maturity,
            "Futures Price": price,
            "Spread vs M1": spread,
            "Spread vs M1 (%)": spread_percentage
        })

    spread_df = pd.DataFrame(spread_rows)

    # Version formatée pour l'affichage.
    spread_display = spread_df.copy()
    spread_display["Futures Price"] = spread_display["Futures Price"].apply(lambda x: f"{x:,.2f}")
    spread_display["Spread vs M1"] = spread_display["Spread vs M1"].apply(lambda x: f"{x:,.2f}")
    spread_display["Spread vs M1 (%)"] = spread_display["Spread vs M1 (%)"].apply(lambda x: f"{x:.2%}")

    st.dataframe(spread_display, width="stretch")

    # Graphique des spreads.
    fig_spreads = px.bar(
        spread_df,
        x="Maturity",
        y="Spread vs M1",
        title="Spreads versus M1"
    )

    fig_spreads.update_layout(
        xaxis_title="Maturity",
        yaxis_title="Spread vs M1",
        height=450
    )

    st.plotly_chart(fig_spreads, width="stretch")

    st.subheader("5. Automatic Interpretation")

    if detected_structure == "Contango":
        st.warning("""
        The curve is in **contango**.

        Interpretation:
        - longer maturities are more expensive than short maturities;
        - this may reflect storage costs, financing costs or expectations of higher future prices;
        - for a long investor rolling the position, the roll yield is generally negative.
        """)

    elif detected_structure == "Backwardation":
        st.success("""
        The curve is in **backwardation**.

        Interpretation:
        - short maturities are more expensive than longer maturities;
        - this may reflect short-term tightness in the physical market;
        - for a long investor rolling the position, the roll yield is generally positive.
        """)

    else:
        st.info("""
        The curve is relatively **flat**.

        Interpretation:
        - futures prices are close across maturities;
        - the market does not show a strong curve slope;
        - the approximate roll yield is close to zero.
        """)

# ============================================================
# TAB 3 - HEDGING SIMULATOR
# ============================================================

with tab3:
    st.header("Hedging Simulator")

    st.markdown("""
    This section simulates a hedge using futures contracts.

    The objective is to compare:
    - the P&L of an unhedged physical exposure;
    - the P&L of the futures position;
    - the net P&L after hedging.

    This module helps explain how a company can reduce commodity price risk
    on a physical exposure.
    """)

    # ========================================================
    # 1. DEFAULT CONTRACT SIZES
    # ========================================================

    default_contract_sizes = {
        "WTI Crude Oil": 1000.0,
        "Brent Crude Oil": 1000.0,
        "Natural Gas": 10000.0,
        "Gold": 100.0,
        "Copper": 25000.0,
        "Wheat": 5000.0,
        "Corn": 5000.0
    }

    default_contract_size = default_contract_sizes.get(selected_commodity, 1.0)

    st.info("""
    Important: the physical quantity and the futures contract size must be expressed in the same unit.
    Example: if the contract size is expressed in barrels, the physical quantity must also be expressed in barrels.
    """)

    # ========================================================
    # 2. PHYSICAL EXPOSURE INPUTS
    # ========================================================

    st.subheader("1. Physical Exposure")

    col1, col2 = st.columns(2)

    with col1:
        exposure_type = st.selectbox(
            "Exposure type",
            [
                "Buyer / Consumer - wants to hedge against a price increase",
                "Producer / Seller - wants to hedge against a price decrease"
            ]
        )

        physical_quantity = st.number_input(
            "Physical quantity exposed",
            min_value=0.0,
            value=10000.0,
            step=100.0
        )

        target_hedge_ratio = st.slider(
            "Target hedge ratio",
            min_value=0.0,
            max_value=1.0,
            value=1.0,
            step=0.05
        )

    with col2:
        spot_initial = st.number_input(
            "Initial spot price",
            min_value=0.0,
            value=float(metrics["last_price"]),
            step=0.1
        )

        spot_final = st.number_input(
            "Simulated final spot price",
            min_value=0.0,
            value=float(metrics["last_price"] * 1.10),
            step=0.1
        )

    # ========================================================
    # 3. FUTURES HEDGE INPUTS
    # ========================================================

    st.subheader("2. Futures Hedge")

    col1, col2 = st.columns(2)

    with col1:
        futures_initial = st.number_input(
            "Initial futures price",
            min_value=0.0,
            value=float(metrics["last_price"]),
            step=0.1
        )

        futures_final = st.number_input(
            "Simulated final futures price",
            min_value=0.0,
            value=float(metrics["last_price"] * 1.10),
            step=0.1
        )

    with col2:
        contract_size = st.number_input(
            "Futures contract size",
            min_value=1.0,
            value=float(default_contract_size),
            step=1.0
        )

        rounding_method = st.selectbox(
            "Contract rounding method",
            ["Nearest", "Floor", "Ceiling"]
        )

    # ========================================================
    # 4. NUMBER OF CONTRACTS
    # ========================================================

    target_hedged_quantity = physical_quantity * target_hedge_ratio
    exact_number_of_contracts = target_hedged_quantity / contract_size

    if rounding_method == "Nearest":
        rounded_number_of_contracts = int(round(exact_number_of_contracts))
    elif rounding_method == "Floor":
        rounded_number_of_contracts = int(np.floor(exact_number_of_contracts))
    else:
        rounded_number_of_contracts = int(np.ceil(exact_number_of_contracts))

    actual_hedged_quantity = rounded_number_of_contracts * contract_size

    if physical_quantity > 0:
        actual_hedge_ratio = actual_hedged_quantity / physical_quantity
    else:
        actual_hedge_ratio = 0.0

    # ========================================================
    # 5. P&L CALCULATION
    # ========================================================

    if exposure_type.startswith("Buyer"):
        hedge_position = "Long futures"

        physical_pnl = -(spot_final - spot_initial) * physical_quantity
        futures_pnl = (futures_final - futures_initial) * rounded_number_of_contracts * contract_size

        if physical_quantity > 0:
            effective_price = (spot_final * physical_quantity - futures_pnl) / physical_quantity
        else:
            effective_price = np.nan

    else:
        hedge_position = "Short futures"

        physical_pnl = (spot_final - spot_initial) * physical_quantity
        futures_pnl = (futures_initial - futures_final) * rounded_number_of_contracts * contract_size

        if physical_quantity > 0:
            effective_price = (spot_final * physical_quantity + futures_pnl) / physical_quantity
        else:
            effective_price = np.nan

    net_pnl = physical_pnl + futures_pnl

    basis_initial = spot_initial - futures_initial
    basis_final = spot_final - futures_final
    basis_change = basis_final - basis_initial

    # ========================================================
    # 6. MAIN HEDGE RESULTS
    # ========================================================

    st.subheader("3. Hedge Results")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Hedge position", hedge_position)
    col2.metric("Exact contracts", format_number(exact_number_of_contracts))
    col3.metric("Rounded contracts", f"{rounded_number_of_contracts}")
    col4.metric("Actual hedge ratio", format_percentage(actual_hedge_ratio))

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Physical P&L", format_number(physical_pnl))
    col2.metric("Futures P&L", format_number(futures_pnl))
    col3.metric("Net P&L", format_number(net_pnl))
    col4.metric("Effective price", format_number(effective_price))

    # ========================================================
    # 7. HEDGE SUMMARY TABLE
    # ========================================================

    summary_df = pd.DataFrame({
        "Indicator": [
            "Physical quantity",
            "Target hedged quantity",
            "Actual hedged quantity",
            "Target hedge ratio",
            "Actual hedge ratio",
            "Initial basis",
            "Final basis",
            "Basis change",
            "Physical P&L",
            "Futures P&L",
            "Net P&L",
            "Effective price"
        ],
        "Value": [
            physical_quantity,
            target_hedged_quantity,
            actual_hedged_quantity,
            target_hedge_ratio,
            actual_hedge_ratio,
            basis_initial,
            basis_final,
            basis_change,
            physical_pnl,
            futures_pnl,
            net_pnl,
            effective_price
        ]
    })

    summary_display = summary_df.copy()

    summary_display["Value"] = summary_display["Value"].apply(
        lambda x: f"{x:,.2f}" if isinstance(x, (int, float, np.floating)) else x
    )

    st.dataframe(summary_display, width="stretch")

    # ========================================================
    # 8. SCENARIO ANALYSIS
    # ========================================================

    st.subheader("4. Scenario Analysis")

    st.markdown("""
    This section compares the unhedged and hedged P&L under different price scenarios.
    """)

    futures_sensitivity = st.slider(
        "Futures sensitivity to spot price movement",
        min_value=0.0,
        max_value=1.5,
        value=1.0,
        step=0.05
    )

    st.caption("""
    A sensitivity of 1 means that the futures price moves exactly like the spot price.
    A sensitivity different from 1 allows the user to simulate basis risk.
    """)

    price_shocks = np.array([-0.20, -0.10, -0.05, 0.00, 0.05, 0.10, 0.20])

    scenario_rows = []

    for shock in price_shocks:
        scenario_spot_final = spot_initial * (1 + shock)
        scenario_futures_final = futures_initial + (scenario_spot_final - spot_initial) * futures_sensitivity

        if exposure_type.startswith("Buyer"):
            scenario_physical_pnl = -(scenario_spot_final - spot_initial) * physical_quantity
            scenario_futures_pnl = (scenario_futures_final - futures_initial) * rounded_number_of_contracts * contract_size

            if physical_quantity > 0:
                scenario_effective_price = (
                    scenario_spot_final * physical_quantity - scenario_futures_pnl
                ) / physical_quantity
            else:
                scenario_effective_price = np.nan

        else:
            scenario_physical_pnl = (scenario_spot_final - spot_initial) * physical_quantity
            scenario_futures_pnl = (futures_initial - scenario_futures_final) * rounded_number_of_contracts * contract_size

            if physical_quantity > 0:
                scenario_effective_price = (
                    scenario_spot_final * physical_quantity + scenario_futures_pnl
                ) / physical_quantity
            else:
                scenario_effective_price = np.nan

        scenario_net_pnl = scenario_physical_pnl + scenario_futures_pnl

        scenario_rows.append({
            "Price shock": shock,
            "Final spot price": scenario_spot_final,
            "Final futures price": scenario_futures_final,
            "Unhedged P&L": scenario_physical_pnl,
            "Futures P&L": scenario_futures_pnl,
            "Hedged P&L": scenario_net_pnl,
            "Effective price": scenario_effective_price
        })

    scenario_df = pd.DataFrame(scenario_rows)

    scenario_display = scenario_df.copy()
    scenario_display["Price shock"] = scenario_display["Price shock"].apply(lambda x: f"{x:.0%}")

    for column in [
        "Final spot price",
        "Final futures price",
        "Unhedged P&L",
        "Futures P&L",
        "Hedged P&L",
        "Effective price"
    ]:
        scenario_display[column] = scenario_display[column].apply(lambda x: f"{x:,.2f}")

    st.dataframe(scenario_display, width="stretch")

    # ========================================================
    # EXCEL EXPORT - HEDGING SIMULATOR
    # ========================================================

    st.subheader("Export Excel")

    st.markdown("""
    This button downloads an Excel file containing the hedge summary
    and the scenario analysis.
    """)

    hedging_excel_report = create_hedging_excel_report(
        summary_df=summary_df,
        scenario_df=scenario_df,
        selected_commodity=selected_commodity,
        selected_period=selected_period
    )

    clean_commodity_name = selected_commodity.lower().replace(" ", "_").replace("/", "_")

    st.download_button(
        label="Download hedging Excel report",
        data=hedging_excel_report,
        file_name=f"hedging_report_{clean_commodity_name}_{selected_period}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    fig_hedge = go.Figure()

    fig_hedge.add_trace(go.Scatter(
        x=scenario_df["Final spot price"],
        y=scenario_df["Unhedged P&L"],
        mode="lines+markers",
        name="Unhedged"
    ))

    fig_hedge.add_trace(go.Scatter(
        x=scenario_df["Final spot price"],
        y=scenario_df["Hedged P&L"],
        mode="lines+markers",
        name="Hedged"
    ))

    fig_hedge.add_trace(go.Scatter(
        x=scenario_df["Final spot price"],
        y=scenario_df["Futures P&L"],
        mode="lines+markers",
        name="Futures P&L"
    ))

    fig_hedge.update_layout(
        title="P&L With and Without Hedge",
        xaxis_title="Final spot price",
        yaxis_title="P&L",
        height=500
    )

    st.plotly_chart(fig_hedge, width="stretch")

    # ========================================================
    # 9. AUTOMATIC INTERPRETATION
    # ========================================================

    st.subheader("5. Automatic Interpretation")

    if exposure_type.startswith("Buyer"):
        st.success("""
        This exposure corresponds to a **buyer hedge**.

        The company needs to buy the commodity in the future.
        It is therefore exposed to a price increase.

        The appropriate hedge is a **long futures** position:
        - if the price increases, the physical purchase cost rises;
        - but the futures position generates a gain;
        - this gain offsets all or part of the increase in the purchase cost.
        """)

    else:
        st.success("""
        This exposure corresponds to a **producer hedge**.

        The company needs to sell the commodity in the future.
        It is therefore exposed to a price decrease.

        The appropriate hedge is a **short futures** position:
        - if the price decreases, the physical sale revenue falls;
        - but the futures position generates a gain;
        - this gain offsets all or part of the decrease in the sale price.
        """)

    if abs(actual_hedge_ratio - target_hedge_ratio) > 0.05:
        st.warning("""
        Warning: the actual hedge ratio is materially different from the target hedge ratio.
        This comes from the rounding of the number of futures contracts.
        """)

    if abs(basis_change) > 0.01:
        st.info("""
        The basis changed between the initial and final prices.
        This illustrates **basis risk**: the spot price and futures price do not always move perfectly together.
        """)


# ============================================================
# TAB 4 - RISK MANAGEMENT
# ============================================================

with tab4:
    st.header("Risk Management")

    st.markdown("""
    This section measures the market risk of the selected commodity.

    Historical returns are used to compute:
    - volatility;
    - Value-at-Risk;
    - Expected Shortfall;
    - stress tests;
    - drawdown.
    """)

    returns = metrics["returns"]

    # ========================================================
    # 1. POSITION PARAMETERS
    # ========================================================

    st.subheader("1. Position Parameters")

    col1, col2 = st.columns(2)

    with col1:
        position_value = st.number_input(
            "Position value",
            min_value=0.0,
            value=100000.0,
            step=1000.0
        )

    with col2:
        position_direction = st.selectbox(
            "Position direction",
            ["Long", "Short"]
        )

    st.markdown("""
    **Reading guide:**

    - A **long** position gains when the commodity price increases.
    - A **short** position gains when the commodity price decreases.
    """)

    # ========================================================
    # 2. HISTORICAL P&L
    # ========================================================

    if position_direction == "Long":
        position_returns = returns
    else:
        position_returns = -returns

    portfolio_pnl = position_returns * position_value
    historical_losses = -portfolio_pnl

    # ========================================================
    # 3. VOLATILITY
    # ========================================================

    daily_volatility = position_returns.std()
    annualized_volatility = daily_volatility * np.sqrt(252)
    annualized_volatility_amount = annualized_volatility * position_value

    # ========================================================
    # 4. VALUE-AT-RISK AND EXPECTED SHORTFALL
    # ========================================================

    var_95 = historical_losses.quantile(0.95)
    var_99 = historical_losses.quantile(0.99)

    expected_shortfall_95 = historical_losses[historical_losses >= var_95].mean()
    expected_shortfall_99 = historical_losses[historical_losses >= var_99].mean()

    worst_daily_loss = historical_losses.max()
    best_daily_gain = portfolio_pnl.max()

    # ========================================================
    # 5. MAIN RISK INDICATORS
    # ========================================================

    st.subheader("2. Main Risk Indicators")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Daily volatility", format_percentage(daily_volatility))
    col2.metric("Annualized volatility", format_percentage(annualized_volatility))
    col3.metric("VaR 95%", format_number(var_95))
    col4.metric("VaR 99%", format_number(var_99))

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Expected Shortfall 95%", format_number(expected_shortfall_95))
    col2.metric("Expected Shortfall 99%", format_number(expected_shortfall_99))
    col3.metric("Worst daily loss", format_number(worst_daily_loss))
    col4.metric("Best daily gain", format_number(best_daily_gain))

    st.markdown("""
    **Interpretation:**

    - **VaR 95%** indicates a daily loss level that should only be exceeded in 5% of cases.
    - **VaR 99%** is more conservative because it focuses on the worst 1% of scenarios.
    - **Expected Shortfall** measures the average loss when the VaR threshold is exceeded.
    """)

    # ========================================================
    # 6. RISK SUMMARY TABLE
    # ========================================================

    st.subheader("3. Risk Summary Table")

    risk_summary_df = pd.DataFrame({
        "Indicator": [
            "Position value",
            "Position direction",
            "Daily volatility",
            "Annualized volatility",
            "Annualized volatility amount",
            "VaR 95%",
            "VaR 99%",
            "Expected Shortfall 95%",
            "Expected Shortfall 99%",
            "Worst daily loss",
            "Best daily gain"
        ],
        "Value": [
            position_value,
            position_direction,
            daily_volatility,
            annualized_volatility,
            annualized_volatility_amount,
            var_95,
            var_99,
            expected_shortfall_95,
            expected_shortfall_99,
            worst_daily_loss,
            best_daily_gain
        ]
    })

    risk_summary_display = risk_summary_df.copy()

    def format_risk_value(value):
        if isinstance(value, str):
            return value
        if pd.isna(value):
            return "N/A"
        return f"{value:,.2f}"

    risk_summary_display["Value"] = risk_summary_display["Value"].apply(format_risk_value)

    st.dataframe(risk_summary_display, width="stretch")

    # ========================================================
    # 7. HISTORICAL P&L DISTRIBUTION
    # ========================================================

    st.subheader("4. Historical P&L Distribution")

    pnl_df = pd.DataFrame({
        "P&L": portfolio_pnl
    })

    fig_pnl_distribution = px.histogram(
        pnl_df,
        x="P&L",
        nbins=60,
        title=f"{selected_commodity} - Daily P&L Distribution"
    )

    fig_pnl_distribution.add_vline(
        x=-var_95,
        line_dash="dash",
        annotation_text="VaR 95%"
    )

    fig_pnl_distribution.add_vline(
        x=-var_99,
        line_dash="dash",
        annotation_text="VaR 99%"
    )

    fig_pnl_distribution.update_layout(
        xaxis_title="Daily P&L",
        yaxis_title="Frequency",
        height=500
    )

    st.plotly_chart(fig_pnl_distribution, width="stretch")

    # ========================================================
    # 8. CUMULATIVE P&L
    # ========================================================

    st.subheader("5. Cumulative P&L")

    cumulative_pnl = portfolio_pnl.cumsum()

    cumulative_pnl_df = pd.DataFrame({
        "Cumulative P&L": cumulative_pnl
    })

    fig_cumulative_pnl = px.line(
        cumulative_pnl_df,
        y="Cumulative P&L",
        title=f"{selected_commodity} - Cumulative Position P&L"
    )

    fig_cumulative_pnl.update_layout(
        xaxis_title="Date",
        yaxis_title="Cumulative P&L",
        height=500
    )

    st.plotly_chart(fig_cumulative_pnl, width="stretch")

    # ========================================================
    # 9. DRAWDOWN
    # ========================================================

    st.subheader("6. Commodity Drawdown")

    st.markdown("""
    Drawdown measures the price decline from the latest historical peak.

    Example:
    if a commodity reaches 100 and then falls to 80, the drawdown is -20%.
    """)

    drawdowns = metrics["drawdowns"]

    drawdown_df = pd.DataFrame({
        "Drawdown": drawdowns
    })

    fig_drawdown = px.line(
        drawdown_df,
        y="Drawdown",
        title=f"{selected_commodity} - Historical Drawdown"
    )

    fig_drawdown.update_layout(
        xaxis_title="Date",
        yaxis_title="Drawdown",
        height=450
    )

    st.plotly_chart(fig_drawdown, width="stretch")

    # ========================================================
    # 10. STRESS TESTS
    # ========================================================

    st.subheader("7. Stress Tests")

    st.markdown("""
    Stress tests simulate the impact of large price moves on the position.

    Example:
    - if the position is long, a price decrease generates a loss;
    - if the position is short, a price increase generates a loss.
    """)

    stress_shocks = np.array([-0.30, -0.20, -0.10, -0.05, 0.05, 0.10, 0.20, 0.30])

    stress_rows = []

    for shock in stress_shocks:

        if position_direction == "Long":
            stress_pnl = shock * position_value
        else:
            stress_pnl = -shock * position_value

        stress_rows.append({
            "Price shock": shock,
            "Stressed P&L": stress_pnl
        })

    stress_df = pd.DataFrame(stress_rows)

    stress_display = stress_df.copy()
    stress_display["Price shock"] = stress_display["Price shock"].apply(lambda x: f"{x:.0%}")
    stress_display["Stressed P&L"] = stress_display["Stressed P&L"].apply(lambda x: f"{x:,.2f}")

    st.dataframe(stress_display, width="stretch")

    fig_stress = px.bar(
        stress_df,
        x="Price shock",
        y="Stressed P&L",
        title="Position Stress Test"
    )

    fig_stress.update_layout(
        xaxis_title="Price shock",
        yaxis_title="P&L",
        height=450
    )

    st.plotly_chart(fig_stress, width="stretch")

    # ========================================================
    # EXCEL EXPORT - RISK MANAGEMENT
    # ========================================================

    st.subheader("Export Excel")

    st.markdown("""
    This button downloads an Excel file containing the main Risk Management results:
    risk summary, historical P&L, cumulative P&L, drawdown and stress tests.
    """)

    risk_excel_report = create_risk_excel_report(
        risk_summary_df=risk_summary_df,
        pnl_df=pnl_df,
        cumulative_pnl_df=cumulative_pnl_df,
        drawdown_df=drawdown_df,
        stress_df=stress_df,
        selected_commodity=selected_commodity,
        selected_period=selected_period
    )

    clean_commodity_name = selected_commodity.lower().replace(" ", "_").replace("/", "_")

    st.download_button(
        label="Download risk Excel report",
        data=risk_excel_report,
        file_name=f"risk_report_{clean_commodity_name}_{selected_period}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # ========================================================
    # 11. AUTOMATIC INTERPRETATION
    # ========================================================

    st.subheader("8. Automatic Interpretation")

    if annualized_volatility < 0.20:
        st.success("""
        Annualized volatility is relatively moderate.

        Historical risk appears limited compared with more volatile commodities.
        """)

    elif annualized_volatility < 0.40:
        st.warning("""
        Annualized volatility is significant.

        The position may experience large variations, which justifies regular risk monitoring.
        """)

    else:
        st.error("""
        Annualized volatility is high.

        This commodity presents significant market risk over the analyzed period.
        """)

    if var_99 > var_95 * 1.5:
        st.info("""
        VaR 99% is significantly higher than VaR 95%.

        This suggests that extreme losses may be much larger than normal daily losses.
        """)

    if position_direction == "Long":
        st.markdown("""
        For a **long** position, the main risk comes from a decrease in the commodity price.
        """)
    else:
        st.markdown("""
        For a **short** position, the main risk comes from an increase in the commodity price.
        """)