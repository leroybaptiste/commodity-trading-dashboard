
# Commodity Trading & Hedging Dashboard
# Version 1 - Niveau 1


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

from src.trade_finance import (
    compute_borrowing_base,
    create_trade_finance_stress_test
)

from src.options_pricer import (
    black_76_price,
    black_76_greeks,
    create_option_payoff_table,
    create_volatility_sensitivity_table
)

# ============================================================
# CONFIGURATION DE LA PAGE STREAMLIT
# ============================================================

st.set_page_config(
    page_title="Commodity Trading & Hedging Dashboard",
    layout="wide"
)

st.title("Commodity Trading & Hedging Dashboard")

st.markdown("""
Dashboard interactif de suivi des marchés de matières premières, construit avec Python et Streamlit.

L'objectif est de reproduire un outil simple de suivi marché, de couverture et de gestion du risque, 
applicable à des problématiques de commodity trading et de hedging.
""")

st.info("""
Le dashboard est structuré en quatre modules : Market Overview, Futures Curve Analysis, 
Hedging Simulator et Risk Management.
""")

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("Dashboard Settings")

st.sidebar.markdown("""
Sélectionne une matière première et une période d'analyse.
Ces paramètres alimentent les modules de marché, de risque et de couverture.
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

st.sidebar.markdown("---")

st.sidebar.markdown(f"""
**Selected commodity**  
{selected_commodity}

**Yahoo Finance ticker**  
{ticker}
""")

st.sidebar.markdown("---")

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

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Market Overview",
    "Futures Curve Analysis",
    "Hedging Simulator",
    "Risk Management",
    "Trade Finance",
    "Options Pricer"
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
    Ce tableau permet de comparer rapidement les principales matières premières suivies dans le dashboard.
    Il donne une vision synthétique du marché avec le dernier prix, la performance, la volatilité,
    le drawdown maximum et la VaR historique.
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
    Cette matrice mesure la corrélation entre les rendements journaliers des différentes matières premières.

    Une corrélation proche de **1** signifie que deux commodities ont tendance à évoluer dans le même sens.  
    Une corrélation proche de **0** signifie qu'il y a peu de relation linéaire.  
    Une corrélation négative signifie qu'elles ont tendance à évoluer en sens opposé.
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
        st.warning("Pas assez de données pour calculer la matrice de corrélation.")
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
        **Interprétation rapide :**

        - Une corrélation élevée entre deux commodities peut indiquer une exposition commune à certains facteurs de marché.
        - Une corrélation faible peut être intéressante dans une logique de diversification.
        - Cette analyse est utile pour comprendre les risques croisés entre plusieurs marchés de matières premières.
        """)
    # ========================================================
    # EXCEL EXPORT - MARKET OVERVIEW
    # ========================================================

    st.subheader("Export Excel")

    st.markdown("""
    Ce bouton permet de télécharger un fichier Excel contenant le tableau de marché,
    la matrice de corrélation et les informations principales du rapport.
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
    Cette partie affiche les prix historiques de la commodity sélectionnée
    et calcule les principaux indicateurs de marché.
    """)

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric(
        "Dernier prix",
        format_number(metrics["last_price"])
    )

    col2.metric(
        "Performance 1 jour",
        format_percentage(metrics["daily_performance"])
    )

    col3.metric(
        "Performance période",
        format_percentage(metrics["period_performance"])
    )

    col4.metric(
        "Volatilité annualisée",
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
        title=f"{selected_commodity} - Prix historique",
        xaxis_title="Date",
        yaxis_title="Prix",
        height=500
    )

    st.plotly_chart(fig_price, width="stretch")

    # Graphique des rendements journaliers.
    returns_df = metrics["returns"].to_frame(name="Daily Returns")

    fig_returns = px.line(
        returns_df,
        y="Daily Returns",
        title=f"{selected_commodity} - Rendements journaliers"
    )

    fig_returns.update_layout(
        xaxis_title="Date",
        yaxis_title="Rendement journalier",
        height=400
    )

    st.plotly_chart(fig_returns, width="stretch")


# ============================================================
# TAB 2 - FUTURES CURVE ANALYSIS
# ============================================================

with tab2:
    st.header("Futures Curve Analysis")

    st.markdown("""
    Cette partie analyse une courbe futures simplifiée.

    En commodity trading, la forme de la courbe futures est très importante :
    - une courbe en **contango** signifie que les prix futures longs sont supérieurs aux prix courts ;
    - une courbe en **backwardation** signifie que les prix futures longs sont inférieurs aux prix courts ;
    - cette structure influence le roll yield, le coût de portage et les stratégies de trading.
    """)

    st.subheader("1. Paramètres de la courbe")

    # On utilise le dernier prix observé comme base de départ.
    # Cela permet d'avoir des valeurs cohérentes avec la commodity sélectionnée.
    base_price = float(metrics["last_price"])

    col1, col2 = st.columns(2)

    with col1:
        curve_scenario = st.selectbox(
            "Scénario de courbe",
            ["Contango", "Backwardation", "Flat"]
        )

    with col2:
        curve_intensity = st.slider(
            "Intensité de la pente",
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

    st.subheader("2. Prix futures par maturité")

    st.markdown("""
    Les prix ci-dessous sont modifiables manuellement.  
    Cela permet de tester différentes formes de courbe futures.
    """)

    curve_prices = []

    cols = st.columns(len(maturities))

    for i, maturity in enumerate(maturities):
        price = cols[i].number_input(
            f"Prix {maturity}",
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

    st.subheader("3. Indicateurs de structure de courbe")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Structure détectée", detected_structure)
    col2.metric("Spread M12 - M1", format_number(spread_m12_m1))
    col3.metric("Pente M12 / M1", format_percentage(curve_slope))
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
        xaxis_title="Maturité",
        yaxis_title="Prix futures",
        height=500
    )

    st.plotly_chart(fig_curve, width="stretch")

    st.subheader("4. Analyse des spreads")

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
        title="Spreads par rapport à M1"
    )

    fig_spreads.update_layout(
        xaxis_title="Maturité",
        yaxis_title="Spread vs M1",
        height=450
    )

    st.plotly_chart(fig_spreads, width="stretch")

    st.subheader("5. Interprétation automatique")

    if detected_structure == "Contango":
        st.warning("""
        La courbe est en **contango**.

        Interprétation :
        - les maturités longues sont plus chères que les maturités courtes ;
        - cela peut refléter des coûts de stockage, de financement ou une anticipation de hausse des prix ;
        - pour un investisseur long qui roule sa position, le roll yield est généralement négatif.
        """)

    elif detected_structure == "Backwardation":
        st.success("""
        La courbe est en **backwardation**.

        Interprétation :
        - les maturités courtes sont plus chères que les maturités longues ;
        - cela peut refléter une tension court terme sur l'offre physique ;
        - pour un investisseur long qui roule sa position, le roll yield est généralement positif.
        """)

    else:
        st.info("""
        La courbe est relativement **flat**.

        Interprétation :
        - les prix futures sont proches entre les maturités ;
        - le marché ne montre pas de pente marquée ;
        - le roll yield approximatif est proche de zéro.
        """)

# ============================================================
# TAB 3 - HEDGING SIMULATOR
# ============================================================

with tab3:
    st.header("Hedging Simulator")

    st.markdown("""
    Cette partie simule une couverture avec contrats futures.

    L'objectif est de comparer :
    - le P&L d'une exposition physique non couverte ;
    - le P&L de la position futures ;
    - le P&L net après couverture.

    Ce module permet de comprendre comment une entreprise peut réduire son risque de prix
    sur une matière première.
    """)

    # ========================================================
    # 1. DEFAULT CONTRACT SIZES
    # ========================================================

    # Taille standard indicative de certains contrats futures.
    # L'objectif est pédagogique : l'utilisateur peut modifier la taille manuellement.
    default_contract_sizes = {
        "WTI Crude Oil": 1000.0,      # 1 contrat WTI CME = 1 000 barils
        "Brent Crude Oil": 1000.0,    # ordre de grandeur classique = 1 000 barils
        "Natural Gas": 10000.0,       # 1 contrat Henry Hub = 10 000 MMBtu
        "Gold": 100.0,                # 1 contrat Gold = 100 onces troy
        "Copper": 25000.0,            # 1 contrat Copper = 25 000 livres
        "Wheat": 5000.0,              # 1 contrat Wheat CBOT = 5 000 bushels
        "Corn": 5000.0                # 1 contrat Corn CBOT = 5 000 bushels
    }

    default_contract_size = default_contract_sizes.get(selected_commodity, 1.0)

    st.info("""
    Important : la quantité physique et la taille du contrat doivent être exprimées dans la même unité.
    Exemple : si le contrat est en barils, la quantité physique doit aussi être en barils.
    """)

    # ========================================================
    # 2. INPUTS DE L'EXPOSITION
    # ========================================================

    st.subheader("1. Exposition physique")

    col1, col2 = st.columns(2)

    with col1:
        exposure_type = st.selectbox(
            "Type d'exposition",
            [
                "Buyer / Consumer - veut se protéger contre une hausse du prix",
                "Producer / Seller - veut se protéger contre une baisse du prix"
            ]
        )

        physical_quantity = st.number_input(
            "Quantité physique exposée",
            min_value=0.0,
            value=10000.0,
            step=100.0
        )

        target_hedge_ratio = st.slider(
            "Hedge ratio cible",
            min_value=0.0,
            max_value=1.0,
            value=1.0,
            step=0.05
        )

    with col2:
        spot_initial = st.number_input(
            "Prix spot initial",
            min_value=0.0,
            value=float(metrics["last_price"]),
            step=0.1
        )

        spot_final = st.number_input(
            "Prix spot final simulé",
            min_value=0.0,
            value=float(metrics["last_price"] * 1.10),
            step=0.1
        )

    # ========================================================
    # 3. INPUTS DE LA COUVERTURE FUTURES
    # ========================================================

    st.subheader("2. Couverture futures")

    col1, col2 = st.columns(2)

    with col1:
        futures_initial = st.number_input(
            "Prix futures initial",
            min_value=0.0,
            value=float(metrics["last_price"]),
            step=0.1
        )

        futures_final = st.number_input(
            "Prix futures final simulé",
            min_value=0.0,
            value=float(metrics["last_price"] * 1.10),
            step=0.1
        )

    with col2:
        contract_size = st.number_input(
            "Taille d'un contrat futures",
            min_value=1.0,
            value=float(default_contract_size),
            step=1.0
        )

        rounding_method = st.selectbox(
            "Méthode d'arrondi du nombre de contrats",
            ["Arrondi au plus proche", "Arrondi inférieur", "Arrondi supérieur"]
        )

    # ========================================================
    # 4. CALCUL DU NOMBRE DE CONTRATS
    # ========================================================

    # Quantité que l'on souhaite couvrir.
    # Formule : Quantité couverte = Quantité physique x Hedge ratio cible
    target_hedged_quantity = physical_quantity * target_hedge_ratio

    # Nombre exact de contrats.
    # Formule : Nombre de contrats = Quantité à couvrir / Taille du contrat
    exact_number_of_contracts = target_hedged_quantity / contract_size

    # En pratique, on ne peut pas toujours prendre 2,4 contrats.
    # Il faut donc arrondir à un nombre entier.
    if rounding_method == "Arrondi au plus proche":
        rounded_number_of_contracts = int(round(exact_number_of_contracts))
    elif rounding_method == "Arrondi inférieur":
        rounded_number_of_contracts = int(np.floor(exact_number_of_contracts))
    else:
        rounded_number_of_contracts = int(np.ceil(exact_number_of_contracts))

    # Quantité réellement couverte après arrondi.
    actual_hedged_quantity = rounded_number_of_contracts * contract_size

    # Hedge ratio réel après arrondi.
    # Il peut être différent du hedge ratio cible.
    if physical_quantity > 0:
        actual_hedge_ratio = actual_hedged_quantity / physical_quantity
    else:
        actual_hedge_ratio = 0.0

    # ========================================================
    # 5. CALCUL DU P&L
    # ========================================================

    # Pour un acheteur/consommateur :
    # - il craint une hausse du prix ;
    # - il se couvre avec une position long futures ;
    # - si le prix monte, la perte physique est compensée par un gain futures.
    #
    # Pour un producteur/vendeur :
    # - il craint une baisse du prix ;
    # - il se couvre avec une position short futures ;
    # - si le prix baisse, la perte physique est compensée par un gain futures.

    if exposure_type.startswith("Buyer"):
        hedge_position = "Long futures"

        # P&L physique pour un acheteur.
        # Si le prix final est supérieur au prix initial, il paie plus cher, donc P&L négatif.
        physical_pnl = -(spot_final - spot_initial) * physical_quantity

        # P&L futures pour une position long.
        # Si le prix futures monte, la position long gagne.
        futures_pnl = (futures_final - futures_initial) * rounded_number_of_contracts * contract_size

        # Prix effectif payé après couverture.
        # Coût physique final = spot_final x quantité.
        # Gain futures réduit ce coût.
        if physical_quantity > 0:
            effective_price = (spot_final * physical_quantity - futures_pnl) / physical_quantity
        else:
            effective_price = np.nan

    else:
        hedge_position = "Short futures"

        # P&L physique pour un producteur.
        # Si le prix final monte, il vend plus cher, donc P&L positif.
        physical_pnl = (spot_final - spot_initial) * physical_quantity

        # P&L futures pour une position short.
        # Si le prix futures baisse, la position short gagne.
        futures_pnl = (futures_initial - futures_final) * rounded_number_of_contracts * contract_size

        # Prix effectif reçu après couverture.
        # Revenu physique final = spot_final x quantité.
        # Gain futures augmente ce revenu.
        if physical_quantity > 0:
            effective_price = (spot_final * physical_quantity + futures_pnl) / physical_quantity
        else:
            effective_price = np.nan

    # P&L net après couverture.
    net_pnl = physical_pnl + futures_pnl

    # Basis initial et final.
    # Basis = Spot - Futures.
    # Le basis risk apparaît si le spot et le futures ne bougent pas parfaitement ensemble.
    basis_initial = spot_initial - futures_initial
    basis_final = spot_final - futures_final
    basis_change = basis_final - basis_initial

    # ========================================================
    # 6. AFFICHAGE DES RÉSULTATS PRINCIPAUX
    # ========================================================

    st.subheader("3. Résultats de la couverture")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Position futures", hedge_position)
    col2.metric("Contrats exacts", format_number(exact_number_of_contracts))
    col3.metric("Contrats arrondis", f"{rounded_number_of_contracts}")
    col4.metric("Hedge ratio réel", format_percentage(actual_hedge_ratio))

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("P&L physique", format_number(physical_pnl))
    col2.metric("P&L futures", format_number(futures_pnl))
    col3.metric("P&L net", format_number(net_pnl))
    col4.metric("Prix effectif", format_number(effective_price))

    # ========================================================
    # 7. TABLEAU DE SYNTHÈSE
    # ========================================================

    summary_df = pd.DataFrame({
        "Indicateur": [
            "Quantité physique",
            "Quantité cible couverte",
            "Quantité réellement couverte",
            "Hedge ratio cible",
            "Hedge ratio réel",
            "Basis initial",
            "Basis final",
            "Variation du basis",
            "P&L physique",
            "P&L futures",
            "P&L net",
            "Prix effectif"
        ],
        "Valeur": [
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

    # Formatage simple pour l'affichage.
    summary_display["Valeur"] = summary_display["Valeur"].apply(
        lambda x: f"{x:,.2f}" if isinstance(x, (int, float, np.floating)) else x
    )

    st.dataframe(summary_display, width="stretch")

    # ========================================================
    # 8. ANALYSE PAR SCÉNARIOS
    # ========================================================

    st.subheader("4. Analyse par scénarios")

    st.markdown("""
    Cette partie compare le P&L sans couverture et avec couverture selon différents scénarios de prix.
    """)

    futures_sensitivity = st.slider(
        "Sensibilité du futures au mouvement du spot",
        min_value=0.0,
        max_value=1.5,
        value=1.0,
        step=0.05
    )

    st.caption("""
    Une sensibilité de 1 signifie que le futures évolue comme le spot.
    Une sensibilité différente de 1 permet de simuler du basis risk.
    """)

    price_shocks = np.array([-0.20, -0.10, -0.05, 0.00, 0.05, 0.10, 0.20])

    scenario_rows = []

    for shock in price_shocks:
        scenario_spot_final = spot_initial * (1 + shock)

        # On simule le prix futures final à partir du mouvement du spot.
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
            "Shock de prix": shock,
            "Prix spot final": scenario_spot_final,
            "Prix futures final": scenario_futures_final,
            "P&L sans couverture": scenario_physical_pnl,
            "P&L futures": scenario_futures_pnl,
            "P&L avec couverture": scenario_net_pnl,
            "Prix effectif": scenario_effective_price
        })

    scenario_df = pd.DataFrame(scenario_rows)

    scenario_display = scenario_df.copy()
    scenario_display["Shock de prix"] = scenario_display["Shock de prix"].apply(lambda x: f"{x:.0%}")

    for column in [
        "Prix spot final",
        "Prix futures final",
        "P&L sans couverture",
        "P&L futures",
        "P&L avec couverture",
        "Prix effectif"
    ]:
        scenario_display[column] = scenario_display[column].apply(lambda x: f"{x:,.2f}")

    st.dataframe(scenario_display, width="stretch")

    # ========================================================
    # EXCEL EXPORT - HEDGING SIMULATOR
    # ========================================================

    st.subheader("Export Excel")

    st.markdown("""
    Ce bouton permet de télécharger un fichier Excel contenant la synthèse de la couverture
    et l'analyse par scénarios.
    """)

    hedging_excel_report = create_hedging_excel_report(
        summary_df=summary_df,
        scenario_df=scenario_df,
        selected_commodity=selected_commodity,
        selected_period=selected_period
    )

    clean_commodity_name = selected_commodity.lower().replace(" ", "_").replace("/", "_")

    st.download_button(
        label="Télécharger le rapport Excel de couverture",
        data=hedging_excel_report,
        file_name=f"hedging_report_{clean_commodity_name}_{selected_period}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Graphique comparant le P&L sans couverture et avec couverture.
    fig_hedge = go.Figure()

    fig_hedge.add_trace(go.Scatter(
        x=scenario_df["Prix spot final"],
        y=scenario_df["P&L sans couverture"],
        mode="lines+markers",
        name="Sans couverture"
    ))

    fig_hedge.add_trace(go.Scatter(
        x=scenario_df["Prix spot final"],
        y=scenario_df["P&L avec couverture"],
        mode="lines+markers",
        name="Avec couverture"
    ))

    fig_hedge.add_trace(go.Scatter(
        x=scenario_df["Prix spot final"],
        y=scenario_df["P&L futures"],
        mode="lines+markers",
        name="P&L futures"
    ))

    fig_hedge.update_layout(
        title="P&L avec et sans couverture",
        xaxis_title="Prix spot final",
        yaxis_title="P&L",
        height=500
    )

    st.plotly_chart(fig_hedge, width="stretch")

    # ========================================================
    # 9. INTERPRÉTATION AUTOMATIQUE
    # ========================================================

    st.subheader("5. Interprétation automatique")

    if exposure_type.startswith("Buyer"):
        st.success("""
        Cette exposition correspond à un **buyer hedge**.

        L'entreprise doit acheter la matière première plus tard.
        Elle craint donc une hausse du prix.

        La couverture adaptée est une position **long futures** :
        - si le prix monte, le coût physique augmente ;
        - mais la position futures génère un gain ;
        - ce gain compense tout ou partie de la hausse du coût d'achat.
        """)

    else:
        st.success("""
        Cette exposition correspond à un **producer hedge**.

        L'entreprise doit vendre la matière première plus tard.
        Elle craint donc une baisse du prix.

        La couverture adaptée est une position **short futures** :
        - si le prix baisse, le revenu physique diminue ;
        - mais la position futures génère un gain ;
        - ce gain compense tout ou partie de la baisse du prix de vente.
        """)

    if abs(actual_hedge_ratio - target_hedge_ratio) > 0.05:
        st.warning("""
        Attention : le hedge ratio réel est assez différent du hedge ratio cible.
        Cela vient de l'arrondi du nombre de contrats futures.
        """)

    if abs(basis_change) > 0.01:
        st.info("""
        Le basis a changé entre le début et la fin de la période.
        Cela illustre le **basis risk** : le spot et le futures ne bougent pas toujours parfaitement ensemble.
        """)


# ============================================================
# TAB 4 - RISK MANAGEMENT
# ============================================================

with tab4:
    st.header("Risk Management")

    st.markdown("""
    Cette partie mesure le risque de marché sur la commodity sélectionnée.

    On utilise les rendements historiques pour calculer :
    - la volatilité ;
    - la Value-at-Risk ;
    - l'Expected Shortfall ;
    - les stress tests ;
    - le drawdown.
    """)

    # On récupère les rendements journaliers déjà calculés.
    returns = metrics["returns"]

    # ========================================================
    # 1. PARAMÈTRES DE LA POSITION
    # ========================================================

    st.subheader("1. Paramètres de la position")

    col1, col2 = st.columns(2)

    with col1:
        position_value = st.number_input(
            "Valeur de la position",
            min_value=0.0,
            value=100000.0,
            step=1000.0
        )

    with col2:
        position_direction = st.selectbox(
            "Sens de la position",
            ["Long", "Short"]
        )

    st.markdown("""
    **Lecture :**

    - Une position **long** gagne lorsque le prix de la commodity monte.
    - Une position **short** gagne lorsque le prix de la commodity baisse.
    """)

    # ========================================================
    # 2. CALCUL DU P&L HISTORIQUE
    # ========================================================

    # Pour une position long :
    # P&L = rendement de la commodity x valeur de la position.
    #
    # Pour une position short :
    # P&L = - rendement de la commodity x valeur de la position.
    #
    # Exemple :
    # si le prix monte de 2 %, une position long gagne 2 %,
    # mais une position short perd 2 %.

    if position_direction == "Long":
        position_returns = returns
    else:
        position_returns = -returns

    # P&L journalier historique en montant.
    portfolio_pnl = position_returns * position_value

    # Les pertes sont l'opposé du P&L.
    # Si le P&L est -2 000, la perte est +2 000.
    historical_losses = -portfolio_pnl

    # ========================================================
    # 3. VOLATILITÉ
    # ========================================================

    # Volatilité journalière : écart-type des rendements journaliers.
    daily_volatility = position_returns.std()

    # Volatilité annualisée :
    # on multiplie la volatilité journalière par racine de 252.
    # 252 correspond approximativement au nombre de jours de trading par an.
    annualized_volatility = daily_volatility * np.sqrt(252)

    # Volatilité en montant.
    annualized_volatility_amount = annualized_volatility * position_value

    # ========================================================
    # 4. VALUE-AT-RISK ET EXPECTED SHORTFALL
    # ========================================================

    # VaR 95 % :
    # perte qui ne devrait être dépassée que dans 5 % des cas.
    var_95 = historical_losses.quantile(0.95)

    # VaR 99 % :
    # perte qui ne devrait être dépassée que dans 1 % des cas.
    var_99 = historical_losses.quantile(0.99)

    # Expected Shortfall 95 % :
    # perte moyenne lorsque la perte dépasse la VaR 95 %.
    expected_shortfall_95 = historical_losses[historical_losses >= var_95].mean()

    # Expected Shortfall 99 % :
    # perte moyenne lorsque la perte dépasse la VaR 99 %.
    expected_shortfall_99 = historical_losses[historical_losses >= var_99].mean()

    # Pire perte journalière observée.
    worst_daily_loss = historical_losses.max()

    # Meilleur gain journalier observé.
    best_daily_gain = portfolio_pnl.max()

    # ========================================================
    # 5. AFFICHAGE DES INDICATEURS PRINCIPAUX
    # ========================================================

    st.subheader("2. Indicateurs de risque principaux")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Volatilité journalière", format_percentage(daily_volatility))
    col2.metric("Volatilité annualisée", format_percentage(annualized_volatility))
    col3.metric("VaR 95 %", format_number(var_95))
    col4.metric("VaR 99 %", format_number(var_99))

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Expected Shortfall 95 %", format_number(expected_shortfall_95))
    col2.metric("Expected Shortfall 99 %", format_number(expected_shortfall_99))
    col3.metric("Pire perte journalière", format_number(worst_daily_loss))
    col4.metric("Meilleur gain journalier", format_number(best_daily_gain))

    st.markdown("""
    **Interprétation :**

    - La **VaR 95 %** indique une perte journalière qui ne devrait être dépassée que dans 5 % des cas.
    - La **VaR 99 %** est plus prudente car elle regarde les 1 % pires scénarios.
    - L'**Expected Shortfall** mesure la perte moyenne dans les cas où la VaR est dépassée.
    """)

    # ========================================================
    # 6. TABLEAU DE SYNTHÈSE
    # ========================================================

    st.subheader("3. Tableau de synthèse du risque")

    risk_summary_df = pd.DataFrame({
        "Indicateur": [
            "Valeur de la position",
            "Sens de la position",
            "Volatilité journalière",
            "Volatilité annualisée",
            "Volatilité annualisée en montant",
            "VaR 95 %",
            "VaR 99 %",
            "Expected Shortfall 95 %",
            "Expected Shortfall 99 %",
            "Pire perte journalière",
            "Meilleur gain journalier"
        ],
        "Valeur": [
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
        """
        Fonction de formatage pour le tableau de risque.
        Elle permet d'afficher proprement les montants et les pourcentages.
        """

        if isinstance(value, str):
            return value
        if pd.isna(value):
            return "N/A"
        return f"{value:,.2f}"

    risk_summary_display["Valeur"] = risk_summary_display["Valeur"].apply(format_risk_value)

    st.dataframe(risk_summary_display, width="stretch")

    # ========================================================
    # 7. DISTRIBUTION DU P&L HISTORIQUE
    # ========================================================

    st.subheader("4. Distribution du P&L historique")

    pnl_df = pd.DataFrame({
        "P&L": portfolio_pnl
    })

    fig_pnl_distribution = px.histogram(
        pnl_df,
        x="P&L",
        nbins=60,
        title=f"{selected_commodity} - Distribution du P&L journalier"
    )

    # Ligne verticale pour la VaR 95 %.
    # Comme la VaR est une perte positive, le niveau de P&L correspondant est -VaR.
    fig_pnl_distribution.add_vline(
        x=-var_95,
        line_dash="dash",
        annotation_text="VaR 95 %"
    )

    # Ligne verticale pour la VaR 99 %.
    fig_pnl_distribution.add_vline(
        x=-var_99,
        line_dash="dash",
        annotation_text="VaR 99 %"
    )

    fig_pnl_distribution.update_layout(
        xaxis_title="P&L journalier",
        yaxis_title="Fréquence",
        height=500
    )

    st.plotly_chart(fig_pnl_distribution, width="stretch")

    # ========================================================
    # 8. ÉVOLUTION DU P&L CUMULÉ
    # ========================================================

    st.subheader("5. Évolution du P&L cumulé")

    # P&L cumulé :
    # on additionne les P&L journaliers dans le temps.
    cumulative_pnl = portfolio_pnl.cumsum()

    cumulative_pnl_df = pd.DataFrame({
        "Cumulative P&L": cumulative_pnl
    })

    fig_cumulative_pnl = px.line(
        cumulative_pnl_df,
        y="Cumulative P&L",
        title=f"{selected_commodity} - P&L cumulé de la position"
    )

    fig_cumulative_pnl.update_layout(
        xaxis_title="Date",
        yaxis_title="P&L cumulé",
        height=500
    )

    st.plotly_chart(fig_cumulative_pnl, width="stretch")

    # ========================================================
    # 9. DRAWDOWN
    # ========================================================

    st.subheader("6. Drawdown de la commodity")

    st.markdown("""
    Le drawdown mesure la baisse du prix depuis son dernier point haut.

    Exemple :
    si une commodity atteint 100 puis baisse à 80, le drawdown est de -20 %.
    """)

    drawdowns = metrics["drawdowns"]

    drawdown_df = pd.DataFrame({
        "Drawdown": drawdowns
    })

    fig_drawdown = px.line(
        drawdown_df,
        y="Drawdown",
        title=f"{selected_commodity} - Drawdown historique"
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

    st.subheader("7. Stress tests")

    st.markdown("""
    Les stress tests simulent l'impact de grands mouvements de prix sur la position.

    Exemple :
    - si la position est long, une baisse de prix génère une perte ;
    - si la position est short, une hausse de prix génère une perte.
    """)

    stress_shocks = np.array([-0.30, -0.20, -0.10, -0.05, 0.05, 0.10, 0.20, 0.30])

    stress_rows = []

    for shock in stress_shocks:

        if position_direction == "Long":
            stress_pnl = shock * position_value
        else:
            stress_pnl = -shock * position_value

        stress_rows.append({
            "Shock de prix": shock,
            "P&L stressé": stress_pnl
        })

    stress_df = pd.DataFrame(stress_rows)

    stress_display = stress_df.copy()
    stress_display["Shock de prix"] = stress_display["Shock de prix"].apply(lambda x: f"{x:.0%}")
    stress_display["P&L stressé"] = stress_display["P&L stressé"].apply(lambda x: f"{x:,.2f}")

    st.dataframe(stress_display, width="stretch")

    fig_stress = px.bar(
        stress_df,
        x="Shock de prix",
        y="P&L stressé",
        title="Stress test de la position"
    )

    fig_stress.update_layout(
        xaxis_title="Shock de prix",
        yaxis_title="P&L",
        height=450
    )

    st.plotly_chart(fig_stress, width="stretch")

    # ========================================================
    # EXCEL EXPORT - RISK MANAGEMENT
    # ========================================================

    st.subheader("Export Excel")

    st.markdown("""
    Ce bouton permet de télécharger un fichier Excel contenant les principaux résultats
    du module Risk Management : synthèse du risque, P&L historique, P&L cumulé,
    drawdown et stress tests.
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
        label="Télécharger le rapport Excel de risque",
        data=risk_excel_report,
        file_name=f"risk_report_{clean_commodity_name}_{selected_period}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    # ========================================================
    # 11. INTERPRÉTATION AUTOMATIQUE
    # ========================================================

    st.subheader("8. Interprétation automatique")

    if annualized_volatility < 0.20:
        st.success("""
        La volatilité annualisée est relativement modérée.
        Le niveau de risque historique semble limité par rapport à d'autres commodities plus volatiles.
        """)

    elif annualized_volatility < 0.40:
        st.warning("""
        La volatilité annualisée est significative.
        La position peut connaître des variations importantes, ce qui justifie un suivi régulier du risque.
        """)

    else:
        st.error("""
        La volatilité annualisée est élevée.
        Cette commodity présente un risque de marché important sur la période analysée.
        """)

    if var_99 > var_95 * 1.5:
        st.info("""
        La VaR 99 % est nettement supérieure à la VaR 95 %.
        Cela suggère que les pertes extrêmes peuvent être beaucoup plus fortes que les pertes courantes.
        """)

    if position_direction == "Long":
        st.markdown("""
        Pour une position **long**, le principal risque vient d'une baisse du prix de la commodity.
        """)
    else:
        st.markdown("""
        Pour une position **short**, le principal risque vient d'une hausse du prix de la commodity.
        """)
# ============================================================
# TAB 5 - TRADE FINANCE / BORROWING BASE
# ============================================================

with tab5:

    st.header("Trade Finance / Borrowing Base")

    st.markdown("""
    Ce module simule le financement d'un stock de matière première.

    Une banque peut financer une entreprise en prenant un stock physique comme collatéral.
    Le montant finançable dépend généralement :
    - de la valeur de marché du stock ;
    - du haircut appliqué par la banque ;
    - de l'advance rate ;
    - du montant déjà emprunté ;
    - de la résistance du collatéral à des stress tests de prix.
    """)

    # ========================================================
    # 1. INPUTS
    # ========================================================

    st.subheader("1. Hypothèses de financement")

    col1, col2 = st.columns(2)

    with col1:
        inventory_quantity = st.number_input(
            "Quantité en stock",
            min_value=0.0,
            value=10000.0,
            step=100.0
        )

        market_price = st.number_input(
            "Prix de marché par unité",
            min_value=0.0,
            value=float(metrics["last_price"]),
            step=0.1
        )

        haircut = st.slider(
            "Haircut appliqué par la banque",
            min_value=0.0,
            max_value=0.50,
            value=0.10,
            step=0.01
        )

    with col2:
        advance_rate = st.slider(
            "Advance rate",
            min_value=0.0,
            max_value=1.00,
            value=0.70,
            step=0.01
        )

        loan_amount = st.number_input(
            "Montant du prêt",
            min_value=0.0,
            value=500000.0,
            step=10000.0
        )

    st.caption("""
    Le haircut réduit la valeur du collatéral prise en compte par la banque.  
    L'advance rate correspond à la part de la valeur éligible que la banque accepte effectivement de financer.
    """)

    # ========================================================
    # 2. CALCULS PRINCIPAUX
    # ========================================================

    trade_finance_results = compute_borrowing_base(
        inventory_quantity=inventory_quantity,
        market_price=market_price,
        haircut=haircut,
        advance_rate=advance_rate,
        loan_amount=loan_amount
    )

    inventory_value = trade_finance_results["inventory_value"]
    eligible_collateral_value = trade_finance_results["eligible_collateral_value"]
    borrowing_base = trade_finance_results["borrowing_base"]
    available_liquidity = trade_finance_results["available_liquidity"]
    loan_to_value = trade_finance_results["loan_to_value"]
    coverage_ratio = trade_finance_results["coverage_ratio"]

    # ========================================================
    # 3. AFFICHAGE DES INDICATEURS
    # ========================================================

    st.subheader("2. Résultats principaux")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Valeur du stock", format_number(inventory_value))
    col2.metric("Valeur éligible", format_number(eligible_collateral_value))
    col3.metric("Borrowing base", format_number(borrowing_base))
    col4.metric("Liquidité disponible", format_number(available_liquidity))

    col1, col2, col3 = st.columns(3)

    col1.metric("Loan-to-Value", format_percentage(loan_to_value))
    col2.metric("Coverage ratio", format_number(coverage_ratio))
    col3.metric("Margin call actuel", "Oui" if loan_amount > borrowing_base else "Non")

    # ========================================================
    # 4. TABLEAU DE SYNTHÈSE
    # ========================================================

    summary_df = pd.DataFrame({
        "Indicateur": [
            "Quantité en stock",
            "Prix de marché",
            "Valeur du stock",
            "Haircut",
            "Valeur éligible après haircut",
            "Advance rate",
            "Borrowing base",
            "Montant du prêt",
            "Liquidité disponible",
            "Loan-to-Value",
            "Coverage ratio"
        ],
        "Valeur": [
            inventory_quantity,
            market_price,
            inventory_value,
            haircut,
            eligible_collateral_value,
            advance_rate,
            borrowing_base,
            loan_amount,
            available_liquidity,
            loan_to_value,
            coverage_ratio
        ]
    })

    summary_display = summary_df.copy()

    summary_display["Valeur"] = summary_display["Valeur"].apply(
        lambda x: f"{x:.2%}" if isinstance(x, float) and 0 <= x <= 1 and summary_display.loc[summary_display["Valeur"] == x, "Indicateur"].iloc[0] in ["Haircut", "Advance rate", "Loan-to-Value"] else f"{x:,.2f}" if isinstance(x, (int, float, np.floating)) else x
    )

    st.dataframe(summary_display, width="stretch")

    # ========================================================
    # 5. STRESS TESTS
    # ========================================================

    st.subheader("3. Stress tests de prix")

    st.markdown("""
    Les stress tests montrent l'impact d'une baisse ou d'une hausse du prix de la commodity
    sur la valeur du stock, la borrowing base et le risque de margin call.
    """)

    shocks = np.array([-0.30, -0.20, -0.10, -0.05, 0.00, 0.05, 0.10, 0.20])

    stress_df = create_trade_finance_stress_test(
        inventory_quantity=inventory_quantity,
        market_price=market_price,
        haircut=haircut,
        advance_rate=advance_rate,
        loan_amount=loan_amount,
        shocks=shocks
    )

    stress_display = stress_df.copy()

    stress_display["Price Shock"] = stress_display["Price Shock"].apply(lambda x: f"{x:.0%}")
    stress_display["Stressed Price"] = stress_display["Stressed Price"].apply(lambda x: f"{x:,.2f}")
    stress_display["Inventory Value"] = stress_display["Inventory Value"].apply(lambda x: f"{x:,.2f}")
    stress_display["Eligible Collateral Value"] = stress_display["Eligible Collateral Value"].apply(lambda x: f"{x:,.2f}")
    stress_display["Borrowing Base"] = stress_display["Borrowing Base"].apply(lambda x: f"{x:,.2f}")
    stress_display["Loan Amount"] = stress_display["Loan Amount"].apply(lambda x: f"{x:,.2f}")
    stress_display["Available Liquidity"] = stress_display["Available Liquidity"].apply(lambda x: f"{x:,.2f}")
    stress_display["Loan-to-Value"] = stress_display["Loan-to-Value"].apply(lambda x: f"{x:.2%}")
    stress_display["Margin Call"] = stress_display["Margin Call"].apply(lambda x: "Oui" if x else "Non")

    st.dataframe(stress_display, width="stretch")

    # Graphique de la borrowing base sous stress.
    fig_borrowing_base = px.line(
        stress_df,
        x="Price Shock",
        y="Borrowing Base",
        markers=True,
        title="Borrowing base sous différents stress de prix"
    )

    fig_borrowing_base.add_hline(
        y=loan_amount,
        line_dash="dash",
        annotation_text="Loan Amount"
    )

    fig_borrowing_base.update_layout(
        xaxis_title="Shock de prix",
        yaxis_title="Borrowing base",
        height=500
    )

    st.plotly_chart(fig_borrowing_base, width="stretch")

    # Graphique de la liquidité disponible.
    fig_liquidity = px.bar(
        stress_df,
        x="Price Shock",
        y="Available Liquidity",
        title="Liquidité disponible après stress"
    )

    fig_liquidity.update_layout(
        xaxis_title="Shock de prix",
        yaxis_title="Liquidité disponible",
        height=450
    )

    st.plotly_chart(fig_liquidity, width="stretch")

    # ========================================================
    # 6. INTERPRÉTATION AUTOMATIQUE
    # ========================================================

    st.subheader("4. Interprétation automatique")

    if loan_amount > borrowing_base:
        st.error("""
        Le montant du prêt dépasse la borrowing base actuelle.

        Cela signifie que le financement n'est pas entièrement couvert par le collatéral éligible.
        Une banque pourrait demander un remboursement partiel, une réduction de l'exposition
        ou un apport de collatéral supplémentaire.
        """)
    else:
        st.success("""
        Le montant du prêt est inférieur à la borrowing base actuelle.

        Le financement semble couvert par la valeur éligible du stock dans le scénario central.
        """)

    stressed_margin_calls = stress_df[stress_df["Margin Call"] == True]

    if not stressed_margin_calls.empty:
        first_margin_call = stressed_margin_calls.iloc[0]

        st.warning(f"""
        Un margin call apparaît dans les scénarios de stress.

        Premier scénario concerné : shock de prix de {first_margin_call["Price Shock"]:.0%}.
        Dans ce cas, la borrowing base devient inférieure au montant du prêt.
        """)
    else:
        st.info("""
        Aucun margin call n'apparaît dans les scénarios de stress test sélectionnés.
        La structure de financement semble relativement résistante aux chocs simulés.
        """)

# ============================================================
# TAB 6 - COMMODITY OPTIONS PRICER
# ============================================================

with tab6:
    st.header("Commodity Options Pricer - Black-76")

    st.markdown("""
    Ce module permet de pricer une option européenne sur contrat futures de matière première
    avec le modèle Black-76.

    Le modèle est adapté aux options sur futures, ce qui le rend pertinent pour les marchés de commodities.
    """)

    # ========================================================
    # 1. INPUTS
    # ========================================================

    st.subheader("1. Paramètres de l'option")

    col1, col2 = st.columns(2)

    with col1:
        option_type = st.selectbox(
            "Type d'option",
            ["Call", "Put"]
        )

        futures_price = st.number_input(
            "Prix futures actuel",
            min_value=0.01,
            value=float(metrics["last_price"]),
            step=0.1
        )

        strike_price = st.number_input(
            "Strike",
            min_value=0.01,
            value=float(metrics["last_price"]),
            step=0.1
        )

    with col2:
        time_to_maturity = st.number_input(
            "Maturité en années",
            min_value=0.01,
            value=0.50,
            step=0.01
        )

        risk_free_rate = st.slider(
            "Taux sans risque",
            min_value=0.00,
            max_value=0.10,
            value=0.03,
            step=0.001
        )

        volatility = st.slider(
            "Volatilité implicite",
            min_value=0.01,
            max_value=1.00,
            value=0.30,
            step=0.01
        )

    # ========================================================
    # 2. PRICING
    # ========================================================

    option_price = black_76_price(
        futures_price=futures_price,
        strike_price=strike_price,
        time_to_maturity=time_to_maturity,
        risk_free_rate=risk_free_rate,
        volatility=volatility,
        option_type=option_type
    )

    greeks = black_76_greeks(
        futures_price=futures_price,
        strike_price=strike_price,
        time_to_maturity=time_to_maturity,
        risk_free_rate=risk_free_rate,
        volatility=volatility,
        option_type=option_type
    )

    st.subheader("2. Résultat du pricing")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Option price", format_number(option_price))
    col2.metric("Delta", f"{greeks['Delta']:.4f}")
    col3.metric("Gamma", f"{greeks['Gamma']:.6f}")
    col4.metric("Vega", format_number(greeks["Vega"]))

    col1, col2 = st.columns(2)

    col1.metric("Theta", format_number(greeks["Theta"]))
    col2.metric("Moneyness", f"{futures_price / strike_price:.2f}x")

    # ========================================================
    # 3. TABLEAU DE SYNTHÈSE
    # ========================================================

    st.subheader("3. Synthèse")

    option_summary_df = pd.DataFrame({
        "Input / Output": [
            "Option type",
            "Futures price",
            "Strike",
            "Time to maturity",
            "Risk-free rate",
            "Implied volatility",
            "Option price",
            "Delta",
            "Gamma",
            "Vega",
            "Theta"
        ],
        "Value": [
            option_type,
            futures_price,
            strike_price,
            time_to_maturity,
            risk_free_rate,
            volatility,
            option_price,
            greeks["Delta"],
            greeks["Gamma"],
            greeks["Vega"],
            greeks["Theta"]
        ]
    })

    st.dataframe(option_summary_df, width="stretch")

    # ========================================================
    # 4. PAYOFF À MATURITÉ
    # ========================================================

    st.subheader("4. Payoff à maturité")

    payoff_df = create_option_payoff_table(
        futures_price=futures_price,
        strike_price=strike_price,
        option_premium=option_price,
        option_type=option_type
    )

    st.dataframe(payoff_df, width="stretch")

    fig_payoff = px.line(
        payoff_df,
        x="Futures Price at Maturity",
        y="Net P&L",
        markers=True,
        title=f"{option_type} option payoff at maturity"
    )

    fig_payoff.add_hline(
        y=0,
        line_dash="dash",
        annotation_text="Break-even"
    )

    fig_payoff.update_layout(
        xaxis_title="Futures price at maturity",
        yaxis_title="Net P&L",
        height=500
    )

    st.plotly_chart(fig_payoff, width="stretch")

    # ========================================================
    # 5. SENSIBILITÉ À LA VOLATILITÉ
    # ========================================================

    st.subheader("5. Sensibilité à la volatilité implicite")

    volatility_range = np.linspace(0.05, 0.80, 20)

    vol_sensitivity_df = create_volatility_sensitivity_table(
        futures_price=futures_price,
        strike_price=strike_price,
        time_to_maturity=time_to_maturity,
        risk_free_rate=risk_free_rate,
        option_type=option_type,
        volatility_range=volatility_range
    )

    fig_vol = px.line(
        vol_sensitivity_df,
        x="Volatility",
        y="Option Price",
        markers=True,
        title="Option price sensitivity to implied volatility"
    )

    fig_vol.update_layout(
        xaxis_title="Implied volatility",
        yaxis_title="Option price",
        height=500
    )

    st.plotly_chart(fig_vol, width="stretch")

    # ========================================================
    # 6. INTERPRÉTATION AUTOMATIQUE
    # ========================================================

    st.subheader("6. Interprétation automatique")

    if option_type == "Call":
        st.info("""
        Un call sur futures donne le droit de bénéficier d'une hausse du prix futures,
        tout en limitant la perte maximale à la prime payée.
        Ce type de stratégie peut être utilisé par un acheteur de commodity qui souhaite se protéger contre une hausse des prix.
        """)
    else:
        st.info("""
        Un put sur futures donne le droit de bénéficier d'une baisse du prix futures,
        tout en limitant la perte maximale à la prime payée.
        Ce type de stratégie peut être utilisé par un producteur ou vendeur de commodity qui souhaite se protéger contre une baisse des prix.
        """)

    if volatility > 0.50:
        st.warning("""
        La volatilité implicite sélectionnée est élevée.
        Cela augmente fortement la valeur de l'option, car l'assurance offerte par l'option devient plus coûteuse.
        """)
    elif volatility < 0.15:
        st.success("""
        La volatilité implicite sélectionnée est faible.
        La prime d'option est relativement moins coûteuse, mais cela peut aussi refléter un marché anticipant peu de mouvements.
        """)
    else:
        st.info("""
        La volatilité implicite sélectionnée se situe dans une zone intermédiaire.
        La prime reflète un niveau de risque modéré sur le futures sous-jacent.
        """)