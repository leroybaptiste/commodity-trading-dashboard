
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

    st.plotly_chart(fig_price, use_container_width=True)

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

    st.plotly_chart(fig_returns, use_container_width=True)


# ============================================================
# TAB 2 - FUTURES CURVE ANALYSIS
# ============================================================

with tab2:
    st.header("Futures Curve Analysis")

    st.markdown("""
    Cette partie permet de construire une courbe futures simple à partir de prix par maturité.

    Pour l'instant, les prix sont entrés manuellement.  
    Plus tard, on pourra automatiser la récupération des contrats futures par maturité.
    """)

    st.subheader("Input de la courbe futures")

    # On utilise le dernier prix comme base pour proposer des valeurs par défaut.
    base_price = float(metrics["last_price"])

    maturities = ["M1", "M2", "M3", "M6", "M12"]

    # Valeurs par défaut légèrement en contango.
    default_curve = {
        "M1": base_price,
        "M2": base_price * 1.005,
        "M3": base_price * 1.010,
        "M6": base_price * 1.020,
        "M12": base_price * 1.040
    }

    curve_prices = []

    cols = st.columns(len(maturities))

    for i, maturity in enumerate(maturities):
        price = cols[i].number_input(
            f"Prix {maturity}",
            min_value=0.0,
            value=float(default_curve[maturity]),
            step=0.1
        )
        curve_prices.append(price)

    curve_df = pd.DataFrame({
        "Maturity": maturities,
        "Futures Price": curve_prices
    })

    # Spread entre la maturité longue et la maturité courte.
    # Si M12 > M1, la courbe est en contango.
    # Si M12 < M1, la courbe est en backwardation.
    spread_m12_m1 = curve_prices[-1] - curve_prices[0]

    if spread_m12_m1 > 0:
        curve_structure = "Contango"
    elif spread_m12_m1 < 0:
        curve_structure = "Backwardation"
    else:
        curve_structure = "Flat"

    # Roll yield pédagogique.
    # Approximation simple :
    # Si la courbe est en backwardation, le roll yield est souvent positif pour un investisseur long.
    # Si la courbe est en contango, le roll yield est souvent négatif pour un investisseur long.
    roll_yield_approx = (curve_prices[0] - curve_prices[-1]) / curve_prices[0]

    col1, col2, col3 = st.columns(3)

    col1.metric("Structure de courbe", curve_structure)
    col2.metric("Spread M12 - M1", format_number(spread_m12_m1))
    col3.metric("Roll yield approx.", format_percentage(roll_yield_approx))

    fig_curve = px.line(
        curve_df,
        x="Maturity",
        y="Futures Price",
        markers=True,
        title=f"{selected_commodity} - Courbe futures simplifiée"
    )

    fig_curve.update_layout(
        xaxis_title="Maturité",
        yaxis_title="Prix futures",
        height=500
    )

    st.plotly_chart(fig_curve, use_container_width=True)

    st.markdown("""
    **Interprétation :**

    - **Contango** : les prix futures longs sont supérieurs aux prix futures courts.
    - **Backwardation** : les prix futures longs sont inférieurs aux prix futures courts.
    - Le **spread M12 - M1** mesure la pente entre la maturité longue et la maturité courte.
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

    st.dataframe(pnl_df, use_container_width=True)

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

    st.dataframe(scenario_df, use_container_width=True)

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

    st.plotly_chart(fig_hedge, use_container_width=True)


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

    st.plotly_chart(fig_hist, use_container_width=True)

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

    st.dataframe(stress_df, use_container_width=True)

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

    st.plotly_chart(fig_stress, use_container_width=True)