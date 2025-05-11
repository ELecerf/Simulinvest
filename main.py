import streamlit as st
import numpy as np
import numpy_financial as npf
import matplotlib.pyplot as plt

# Fonction pour calculer les résultats des stratégies
def calculer_strategies(params):
    prix_paris = params['prix_paris']
    apport = params['apport']
    taux_credit = params['taux_credit'] / 100
    duree_credit = params['duree_credit']
    rendement_bourse = params['rendement_bourse'] / 100
    horizon = params['horizon']

    # Stratégie 1 : Immobilier à Paris
    montant_credit = prix_paris - apport
    mensualite = -npf.pmt(taux_credit / 12, duree_credit * 12, montant_credit)
    flux_immo = [-apport] + [-mensualite * 12] * duree_credit + [prix_paris * 1.02 ** horizon]  # Valorisation à +2%/an
    irr_immo = npf.irr(flux_immo) * 100
    patrimoine_immo = prix_paris * (1.02 ** horizon) - montant_credit * (1 + taux_credit) ** horizon

    # Stratégie 2 : Bourse
    flux_bourse = [-prix_paris] + [0] * (horizon - 1) + [prix_paris * (1 + rendement_bourse) ** horizon]
    irr_bourse = npf.irr(flux_bourse) * 100
    patrimoine_bourse = prix_paris * (1 + rendement_bourse) ** horizon

    # Stratégie 3 : Sans investissement
    flux_sans = [-prix_paris] + [0] * horizon
    irr_sans = npf.irr(flux_sans) * 100
    patrimoine_sans = prix_paris

    # Évolution du patrimoine pour le graphique
    temps = np.arange(horizon + 1)
    patrimoine_immo_t = [apport + prix_paris * (1.02 ** t) - montant_credit * (1 + taux_credit) ** t for t in temps]
    patrimoine_bourse_t = [prix_paris * (1 + rendement_bourse) ** t for t in temps]
    patrimoine_sans_t = [prix_paris] * (horizon + 1)

    return {
        'irr_immo': irr_immo, 'patrimoine_immo': patrimoine_immo, 'patrimoine_immo_t': patrimoine_immo_t,
        'irr_bourse': irr_bourse, 'patrimoine_bourse': patrimoine_bourse, 'patrimoine_bourse_t': patrimoine_bourse_t,
        'irr_sans': irr_sans, 'patrimoine_sans': patrimoine_sans, 'patrimoine_sans_t': patrimoine_sans_t,
        'temps': temps
    }

# Interface Streamlit
st.title("Comparateur de Stratégies d’Investissement")

# Barre latérale pour les paramètres
st.sidebar.header("Paramètres")
prix_paris = st.sidebar.number_input("Prix de la résidence (€)", min_value=100000, value=680000, step=10000)
apport = st.sidebar.number_input("Apport initial (€)", min_value=0, value=150000, step=5000)
taux_credit = st.sidebar.slider("Taux de crédit annuel (%)", 0.5, 5.0, 2.0, 0.1)
duree_credit = st.sidebar.slider("Durée du crédit (années)", 5, 30, 20, 1)
rendement_bourse = st.sidebar.slider("Rendement annuel bourse (%)", 1.0, 10.0, 5.0, 0.5)
horizon = st.sidebar.slider("Horizon d’investissement (années)", 5, 40, 20, 1)

# Bouton pour lancer les calculs
if st.sidebar.button("Calculer"):
    params = {
        'prix_paris': prix_paris,
        'apport': apport,
        'taux_credit': taux_credit,
        'duree_credit': duree_credit,
        'rendement_bourse': rendement_bourse,
        'horizon': horizon
    }
    resultats = calculer_strategies(params)

    # Affichage des résultats
    st.header("Résultats")
    st.write(f"**Stratégie 1 - Immobilier :** TRI = {resultats['irr_immo']:.2f}% | Patrimoine net = {resultats['patrimoine_immo']:,.0f} €")
    st.write(f"**Stratégie 2 - Bourse :** TRI = {resultats['irr_bourse']:.2f}% | Patrimoine net = {resultats['patrimoine_bourse']:,.0f} €")
    st.write(f"**Stratégie 3 - Sans investissement :** TRI = {resultats['irr_sans']:.2f}% | Patrimoine net = {resultats['patrimoine_sans']:,.0f} €")

    # Graphique : Évolution du patrimoine
    st.header("Évolution du Patrimoine")
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(resultats['temps'], resultats['patrimoine_immo_t'], label="Immobilier", color="blue")
    ax.plot(resultats['temps'], resultats['patrimoine_bourse_t'], label="Bourse", color="green")
    ax.plot(resultats['temps'], resultats['patrimoine_sans_t'], label="Sans investissement", color="red")
    ax.set_xlabel("Années")
    ax.set_ylabel("Patrimoine (€)")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)

# Bouton de réinitialisation
if st.sidebar.button("Réinitialiser"):
    st.experimental_rerun()  # Relance l’app pour réinitialiser les valeurs par défaut
