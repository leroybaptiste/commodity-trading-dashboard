import pandas as pd
import numpy as np


# ============================================================
# TRADE FINANCE / BORROWING BASE FUNCTIONS
# ============================================================

def compute_borrowing_base(
    inventory_quantity,
    market_price,
    haircut,
    advance_rate,
    loan_amount
):
    """
    Calcule les principaux indicateurs de financement de stock.

    inventory_quantity : quantité de commodity détenue en stock
    market_price : prix de marché par unité
    haircut : décote appliquée par la banque
    advance_rate : pourcentage de la valeur éligible que la banque accepte de financer
    loan_amount : montant déjà emprunté ou demandé
    """

    # Valeur brute du stock.
    # Formule : quantité x prix de marché
    inventory_value = inventory_quantity * market_price

    # Valeur après haircut.
    # Le haircut sert à protéger la banque contre une baisse de prix ou un risque de liquidité.
    eligible_collateral_value = inventory_value * (1 - haircut)

    # Borrowing base.
    # C'est le montant maximum que la banque accepte de prêter contre ce stock.
    borrowing_base = eligible_collateral_value * advance_rate

    # Capacité disponible.
    # Si positive, l'entreprise peut encore emprunter.
    # Si négative, elle est surfinancée par rapport à la borrowing base.
    available_liquidity = borrowing_base - loan_amount

    # Loan-to-value.
    # Mesure le niveau de dette par rapport à la valeur brute du stock.
    if inventory_value > 0:
        loan_to_value = loan_amount / inventory_value
    else:
        loan_to_value = np.nan

    # Coverage ratio.
    # Mesure combien de fois la borrowing base couvre le montant du prêt.
    if loan_amount > 0:
        coverage_ratio = borrowing_base / loan_amount
    else:
        coverage_ratio = np.nan

    return {
        "inventory_value": inventory_value,
        "eligible_collateral_value": eligible_collateral_value,
        "borrowing_base": borrowing_base,
        "available_liquidity": available_liquidity,
        "loan_to_value": loan_to_value,
        "coverage_ratio": coverage_ratio
    }


def create_trade_finance_stress_test(
    inventory_quantity,
    market_price,
    haircut,
    advance_rate,
    loan_amount,
    shocks
):
    """
    Crée un tableau de stress test.

    L'objectif est de voir ce qui arrive à la borrowing base
    si le prix de la commodity baisse ou augmente.
    """

    stress_rows = []

    for shock in shocks:

        # Prix stressé après variation de prix.
        stressed_price = market_price * (1 + shock)

        # Valeur du stock dans le scénario stressé.
        inventory_value = inventory_quantity * stressed_price

        # Valeur éligible après haircut.
        eligible_collateral_value = inventory_value * (1 - haircut)

        # Borrowing base stressée.
        borrowing_base = eligible_collateral_value * advance_rate

        # Différence entre borrowing base et dette.
        available_liquidity = borrowing_base - loan_amount

        # Margin call si la borrowing base devient inférieure au prêt.
        margin_call = loan_amount > borrowing_base

        if inventory_value > 0:
            loan_to_value = loan_amount / inventory_value
        else:
            loan_to_value = np.nan

        stress_rows.append({
            "Price Shock": shock,
            "Stressed Price": stressed_price,
            "Inventory Value": inventory_value,
            "Eligible Collateral Value": eligible_collateral_value,
            "Borrowing Base": borrowing_base,
            "Loan Amount": loan_amount,
            "Available Liquidity": available_liquidity,
            "Loan-to-Value": loan_to_value,
            "Margin Call": margin_call
        })

    return pd.DataFrame(stress_rows)
