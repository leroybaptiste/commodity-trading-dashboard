import streamlit as st

st.set_page_config(
    page_title="Commodity Trading & Hedging Dashboard",
    layout="wide"
)

st.title("Commodity Trading & Hedging Dashboard")

st.write("Projet initialisé avec succès.")

st.markdown("""
### Objectif du projet

Créer un dashboard permettant de suivre les marchés de matières premières, 
d’analyser les prix, la volatilité, les courbes futures et de simuler des stratégies de couverture.

### Modules prévus

1. Market Overview  
2. Futures Curve Analysis  
3. Hedging Simulator  
4. Risk Management  
""")
