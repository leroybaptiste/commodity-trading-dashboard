
# Commodity Trading & Hedging Dashboard
# Version 1 - Niveau 1


# Streamlit sert à créer l'application web interactive.
import streamlit as st

# pandas sert à manipuler les tableaux de données.
import pandas as pd

# numpy sert aux calculs mathématiques.
import numpy as np

# yfinance permet de récupérer des données de marché depuis Yahoo Finance.
import yfinance as yf

# plotly sert à créer des graphiques interactifs.
import plotly.graph_objects as go
import plotly.express as px


# ============================================================
# CONFIGURATION DE LA PAGE STREAMLIT
# ============================================================

st.set_page_config(
    page_title="Commodity Trading & Hedging Dashboard",
    layout="wide"
)

st.title("Commodity Trading & Hedging Dashboard")

st.markdown("""
Ce dashboard permet de suivre des matières premières, d'analyser les prix,
de visualiser une courbe futures, de simuler une couverture et de calculer
des indicateurs de risque.
""")


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
    Cette fonction télécharge les prix historiques d'une commodity.

    ticker : code Yahoo Finance, par exemple CL=F pour le WTI.
    period : période choisie, par exemple 1y pour 1 an.

    @st.cache_data permet de garder les données en mémoire pendant 1 heure.
    Cela évite de télécharger les mêmes données à chaque interaction.
    """

    data = yf.download(
        ticker,
        period=period,
        interval="1d",
        auto_adjust=True,
        progress=False
    )

    # Si aucune donnée n'est récupérée, on retourne une série vide.
    if data.empty:
        return pd.Series(dtype=float)

    # Yahoo Finance peut parfois renvoyer des colonnes simples ou multi-index.
    # On récupère uniquement la colonne Close, c'est-à-dire le prix de clôture.
    try:
        close_prices = data["Close"]
    except KeyError:
        return pd.Series(dtype=float)

    # Si close_prices est un DataFrame, on prend la première colonne.
    # Cela peut arriver avec certains formats de données Yahoo Finance.
    if isinstance(close_prices, pd.DataFrame):
        close_prices = close_prices.iloc[:, 0]

    # On supprime les valeurs manquantes.
    close_prices = close_prices.dropna()

    # On donne un nom clair à la série.
    close_prices.name = "Price"

    return close_prices


# ============================================================
# FONCTION DE CALCUL DES MÉTRIQUES DE MARCHÉ
# ============================================================

def compute_market_metrics(price_series):
    """
    Cette fonction calcule les principaux indicateurs de marché.

    price_series : série de prix historiques.
    """

    # Les rendements journaliers mesurent la variation quotidienne du prix.
    # Formule : Return_t = Price_t / Price_t-1 - 1
    returns = price_series.pct_change().dropna()

    # Dernier prix disponible.
    last_price = price_series.iloc[-1]

    # Prix au début de la période sélectionnée.
    first_price = price_series.iloc[0]

    # Performance totale sur la période.
    # Formule : Perf = Dernier prix / Premier prix - 1
    period_performance = last_price / first_price - 1

    # Performance journalière.
    if len(price_series) > 1:
        daily_performance = last_price / price_series.iloc[-2] - 1
    else:
        daily_performance = np.nan

    # Volatilité annualisée.
    # On prend l'écart-type des rendements journaliers et on multiplie par racine de 252.
    # 252 correspond approximativement au nombre de jours de trading dans une année.
    annualized_volatility = returns.std() * np.sqrt(252)

    # Maximum drawdown.
    # Le drawdown mesure la baisse depuis un plus haut historique.
    running_max = price_series.cummax()
    drawdowns = price_series / running_max - 1
    max_drawdown = drawdowns.min()

    # VaR historique à 95%.
    # On prend le quantile 5% des rendements.
    # Cela donne une perte journalière qui ne devrait être dépassée que dans 5% des cas.
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
# FONCTIONS D'AFFICHAGE
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
    Format simple pour afficher un nombre avec deux décimales.
    """

    if pd.isna(value):
        return "N/A"
    return f"{value:,.2f}"


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("Paramètres")

selected_commodity = st.sidebar.selectbox(
    "Commodity",
    list(COMMODITY_TICKERS.keys())
)

selected_period = st.sidebar.selectbox(
    "Période historique",
    ["1mo", "3mo", "6mo", "1y", "3y", "5y"],
    index=3
)

ticker = COMMODITY_TICKERS[selected_commodity]


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
    "Futures Curve Analysis",
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

    Exemple :
    - une entreprise qui doit acheter une matière première craint une hausse du prix ;
    - elle peut prendre une position long futures pour se couvrir ;
    - une entreprise qui vend une matière première craint une baisse du prix ;
    - elle peut prendre une position short futures pour se couvrir.
    """)

    st.subheader("Hypothèses de couverture")

    col1, col2 = st.columns(2)

    with col1:
        exposure_type = st.selectbox(
            "Type d'exposition",
            [
                "Buyer / Consumer - risque de hausse du prix",
                "Producer / Seller - risque de baisse du prix"
            ]
        )

        quantity = st.number_input(
            "Quantité physique à couvrir",
            min_value=0.0,
            value=10000.0,
            step=100.0
        )

        contract_size = st.number_input(
            "Taille d'un contrat futures",
            min_value=1.0,
            value=50.0,
            step=1.0
        )

        hedge_ratio = st.slider(
            "Hedge ratio",
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

        futures_initial = st.number_input(
            "Prix futures initial",
            min_value=0.0,
            value=float(metrics["last_price"]),
            step=0.1
        )

        final_price = st.number_input(
            "Prix spot final simulé",
            min_value=0.0,
            value=float(metrics["last_price"] * 1.10),
            step=0.1
        )

        futures_final = st.number_input(
            "Prix futures final simulé",
            min_value=0.0,
            value=float(metrics["last_price"] * 1.10),
            step=0.1
        )

    # Quantité réellement couverte.
    hedged_quantity = quantity * hedge_ratio

    # Nombre théorique de contrats futures.
    # Formule : N = quantité à couvrir / taille d'un contrat
    number_of_contracts_exact = hedged_quantity / contract_size

    # En pratique, on ne peut pas toujours acheter 200,4 contrats.
    # On arrondit donc au contrat entier le plus proche.
    number_of_contracts = round(number_of_contracts_exact)

    # P&L physique.
    # Pour un acheteur, si le prix monte, c'est une perte car son coût d'achat augmente.
    # Pour un producteur/vendeur, si le prix monte, c'est un gain car il vend plus cher.
    if exposure_type.startswith("Buyer"):
        physical_pnl = -(final_price - spot_initial) * quantity
        futures_pnl = (futures_final - futures_initial) * number_of_contracts * contract_size
        hedge_position = "Long futures"
    else:
        physical_pnl = (final_price - spot_initial) * quantity
        futures_pnl = (futures_initial - futures_final) * number_of_contracts * contract_size
        hedge_position = "Short futures"

    net_pnl = physical_pnl + futures_pnl

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Position de couverture", hedge_position)
    col2.metric("Nombre de contrats", f"{number_of_contracts}")
    col3.metric("P&L sans couverture", format_number(physical_pnl))
    col4.metric("P&L avec couverture", format_number(net_pnl))

    st.subheader("Détail du P&L")

    pnl_df = pd.DataFrame({
        "Composante": ["P&L physique", "P&L futures", "P&L net"],
        "Montant": [physical_pnl, futures_pnl, net_pnl]
    })

    st.dataframe(pnl_df, width="stretch")

    # Création d'un scénario de prix pour comparer sans couverture vs avec couverture.
    scenario_prices = np.array([
        spot_initial * 0.80,
        spot_initial * 0.90,
        spot_initial,
        spot_initial * 1.10,
        spot_initial * 1.20
    ])

    scenario_rows = []

    for scenario_price in scenario_prices:
        scenario_futures_final = scenario_price

        if exposure_type.startswith("Buyer"):
            scenario_physical_pnl = -(scenario_price - spot_initial) * quantity
            scenario_futures_pnl = (scenario_futures_final - futures_initial) * number_of_contracts * contract_size
        else:
            scenario_physical_pnl = (scenario_price - spot_initial) * quantity
            scenario_futures_pnl = (futures_initial - scenario_futures_final) * number_of_contracts * contract_size

        scenario_net_pnl = scenario_physical_pnl + scenario_futures_pnl

        scenario_rows.append({
            "Prix final": scenario_price,
            "P&L sans couverture": scenario_physical_pnl,
            "P&L futures": scenario_futures_pnl,
            "P&L avec couverture": scenario_net_pnl
        })

    scenario_df = pd.DataFrame(scenario_rows)

    st.subheader("Analyse par scénarios")

    st.dataframe(scenario_df, width="stretch")

    fig_hedge = go.Figure()

    fig_hedge.add_trace(go.Scatter(
        x=scenario_df["Prix final"],
        y=scenario_df["P&L sans couverture"],
        mode="lines+markers",
        name="Sans couverture"
    ))

    fig_hedge.add_trace(go.Scatter(
        x=scenario_df["Prix final"],
        y=scenario_df["P&L avec couverture"],
        mode="lines+markers",
        name="Avec couverture"
    ))

    fig_hedge.update_layout(
        title="Comparaison P&L avec et sans couverture",
        xaxis_title="Prix final",
        yaxis_title="P&L",
        height=500
    )

    st.plotly_chart(fig_hedge, width="stretch")


# ============================================================
# TAB 4 - RISK MANAGEMENT
# ============================================================

with tab4:
    st.header("Risk Management")

    st.markdown("""
    Cette partie calcule des indicateurs de risque sur la commodity sélectionnée :
    volatilité, VaR historique, Expected Shortfall et stress tests.
    """)

    returns = metrics["returns"]

    st.subheader("Paramètres de risque")

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

    # VaR historique à 95%.
    # Pour une position long, une baisse du prix génère une perte.
    # Pour une position short, une hausse du prix génère une perte.
    if position_direction == "Long":
        var_return = returns.quantile(0.05)
        expected_shortfall_return = returns[returns <= var_return].mean()
    else:
        var_return = returns.quantile(0.95)
        expected_shortfall_return = returns[returns >= var_return].mean()

    # Conversion en montant.
    # On met un signe positif pour afficher la perte potentielle.
    if position_direction == "Long":
        var_amount = -var_return * position_value
        expected_shortfall_amount = -expected_shortfall_return * position_value
    else:
        var_amount = var_return * position_value
        expected_shortfall_amount = expected_shortfall_return * position_value

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Volatilité annualisée", format_percentage(metrics["annualized_volatility"]))
    col2.metric("VaR 95% journalière", format_number(var_amount))
    col3.metric("Expected Shortfall", format_number(expected_shortfall_amount))
    col4.metric("Max Drawdown", format_percentage(metrics["max_drawdown"]))

    st.markdown("""
    **Lecture rapide :**

    - La **VaR 95%** estime une perte journalière qui ne devrait être dépassée que dans 5% des cas.
    - L'**Expected Shortfall** mesure la perte moyenne dans les pires scénarios au-delà de la VaR.
    - Le **Max Drawdown** mesure la pire baisse depuis un point haut historique.
    """)

    st.subheader("Distribution des rendements journaliers")

    fig_hist = px.histogram(
        returns,
        nbins=50,
        title=f"{selected_commodity} - Distribution des rendements journaliers"
    )

    fig_hist.update_layout(
        xaxis_title="Rendement journalier",
        yaxis_title="Fréquence",
        height=450
    )

    st.plotly_chart(fig_hist, width="stretch")

    st.subheader("Stress tests")

    shocks = [-0.20, -0.10, -0.05, 0.05, 0.10, 0.20]

    stress_rows = []

    for shock in shocks:
        if position_direction == "Long":
            stress_pnl = shock * position_value
        else:
            stress_pnl = -shock * position_value

        stress_rows.append({
            "Shock de prix": shock,
            "P&L stressé": stress_pnl
        })

    stress_df = pd.DataFrame(stress_rows)

    stress_df["Shock de prix"] = stress_df["Shock de prix"].apply(lambda x: f"{x:.0%}")

    st.dataframe(stress_df, width="stretch")

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