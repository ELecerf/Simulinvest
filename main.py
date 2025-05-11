# streamlit_app.py
import streamlit as st
import numpy as np
import numpy_financial as npf
import matplotlib.pyplot as plt

# --------------------- Fonctions utilitaires ---------------------
def ann_to_month(rate):
    """Convertit un taux annuel en taux mensuel composé équivalent."""
    return (1 + rate) ** (1 / 12) - 1

def tri_annualise(flux_mensuels):
    irr_m = npf.irr(flux_mensuels)
    return (1 + irr_m) ** 12 - 1 if irr_m is not None else np.nan

# --------------------- Calcul complet des 3 stratégies ---------------------
def run_simulation(params):
    # Dilate les paramètres
    p           = params
    n_months    = p['horizon'] * 12
    t_mens      = p['taux_credit'] / 100 / 12
    tm_bourse_2 = ann_to_month(p['rdt_bourse_2'] / 100)
    tm_bourse_3 = ann_to_month(p['rdt_bourse_3'] / 100)

    # === STRATÉGIE 1 : Achat RP Paris ===
    apport      = p['prix_paris'] * p['apport_pct'] / 100
    frais_not   = p['prix_paris'] * p['frais_not_pct'] / 100
    emprunt_P   = p['prix_paris'] + frais_not - apport
    mens_P      = -npf.pmt(t_mens, n_months, emprunt_P)
    effort_ref  = mens_P + p['charges_paris_0']

    flux_A = [-(apport + frais_not)]
    charges_P  = p['charges_paris_0']
    loyer_imput = p['loyer_paris_0']

    patr_A_t = [-(apport + frais_not)]
    capital_restant_P = emprunt_P

    for m in range(1, n_months + 1):
        inflow  = loyer_imput
        int_pmt = capital_restant_P * t_mens
        amort   = mens_P - int_pmt
        capital_restant_P -= amort
        outflow = mens_P + charges_P
        flux_A.append(inflow - outflow)

        # Patrimoine instantané = valeur bien – dette
        valeur_bien = p['prix_paris'] * (1 + p['appr_paris']/100) ** (m/12)
        patr_A_t.append(valeur_bien - capital_restant_P)

        if m % 12 == 0:
            loyer_imput *= 1 + p['inflation']/100
            charges_P   *= 1 + p['inflation']/100

    # Valeur finale (revente)
    valeur_finale_P = p['prix_paris'] * (1 + p['appr_paris']/100) ** p['horizon']
    flux_A[-1] += valeur_finale_P
    patr_final_A = patr_A_t[-1]

    irr_A = tri_annualise(flux_A)

    # === STRATÉGIE 2 : Location + Bourse ===
    flux_B = [-apport]
    port_B = apport
    loyer_P = p['loyer_paris_0']
    patr_B_t = [apport]

    for m in range(1, n_months + 1):
        diff = effort_ref - loyer_P   # écart mensuel à investir
        port_B = (port_B + diff) * (1 + tm_bourse_2)
        flux_B.append(-diff)
        patr_B_t.append(port_B)
        if m % 12 == 0:
            loyer_P *= 1 + p['inflation']/100

    flux_B[-1] += port_B
    irr_B = tri_annualise(flux_B)
    patr_final_B = port_B

    # === STRATÉGIE 3 : Location + Locatif + Bourse ===
    frais_not_L = p['prix_loc'] * p['frais_not_pct']/100
    emprunt_L   = p['prix_loc'] + frais_not_L - apport
    mens_L      = -npf.pmt(t_mens, n_months, emprunt_L)
    loyer_brut  = p['prix_loc'] * p['rend_brut']/100 / 12

    flux_C = [-apport]
    port_C = 0
    loyer_P = p['loyer_paris_0']
    loyer_n = loyer_brut
    dette_L = emprunt_L
    patr_C_t = [-apport]

    for m in range(1, n_months + 1):
        # Loyers nets après vacance & charges
        lo_net = loyer_n * (1 - p['vacance']) * (1 - p['charges_exploit']) - p['taxe_fonc']/12
        int_L  = dette_L * t_mens
        amortL = mens_L - int_L
        dette_L -= amortL
        cashflow = lo_net - mens_L
        effort   = effort_ref - loyer_P
        invest   = max(0, effort + cashflow)
        port_C   = (port_C + invest) * (1 + tm_bourse_3)

        # Patrimoine instantané
        valeur_loc = p['prix_loc'] * (1 + p['appr_loc']/100) ** (m/12)
        patr_C_t.append(valeur_loc + port_C - dette_L)
        flux_C.append(-invest)

        if m % 12 == 0:
            loyer_P *= 1 + p['inflation']/100
            loyer_n *= 1 + p['inflation']/100

    valeur_finale_L = p['prix_loc'] * (1 + p['appr_loc']/100) ** p['horizon']
    flux_C[-1] += valeur_finale_L + port_C
    patr_final_C = valeur_finale_L + port_C - 0  # dette nulle

    irr_C = tri_annualise(flux_C)

    # Packaging résultats
    temps = np.arange(p['horizon']*12 + 1) / 12  # en années
    return {
        "IRR_A": irr_A, "IRR_B": irr_B, "IRR_C": irr_C,
        "patr_A": patr_final_A, "patr_B": patr_final_B, "patr_C": patr_final_C,
        "courbes": {
            "Achat Paris": patr_A_t,
            "Bourse": patr_B_t,
            "Locatif + Bourse": patr_C_t
        },
        "temps": temps
    }

# --------------------- Interface Streamlit ---------------------
st.title("📊 Comparateur de Stratégies : Acheter, Louer + Bourse, Louer + Locatif")

with st.sidebar:
    st.header("Paramètres principaux")
    prix_paris     = st.number_input("Prix du bien à Paris (€)", 200_000, 2_000_000, 680_000, 10_000)
    loyer_paris_0  = st.number_input("Loyer marché équivalent (€ / mois)", 500, 4_000, 1_860, 50)
    charges_paris  = st.number_input("Charges propres (€/mois)", 100, 2_000, 941, 10)
    prix_loc       = st.number_input("Prix du locatif au Mans (€)", 50_000, 300_000, 100_000, 5_000)
    rend_brut      = st.slider("Rendement locatif brut (%)", 4.0, 12.0, 10.0, 0.1)
    rdt_bourse_2   = st.slider("Rendement annuel bourse strat. 2 (%)", 3.0, 10.0, 5.0, 0.1)
    rdt_bourse_3   = st.slider("Rendement annuel bourse strat. 3 (%)", 3.0, 10.0, 5.0, 0.1)
    horizon        = st.slider("Horizon (années)", 10, 40, 30, 1)

    st.subheader("Hypothèses secondaires")
    inflation      = st.number_input("Inflation loyers & charges (%)", 0.0, 3.0, 1.5, 0.1)
    appr_paris     = st.number_input("Appréciation Paris (%)", 0.0, 3.0, 0.8, 0.1)
    appr_loc       = st.number_input("Appréciation locatif (%)", 0.0, 3.0, 1.0, 0.1)
    vacance        = st.slider("Vacance locative (mois/an)", 0, 6, 1, 1) / 12
    charges_expl   = st.slider("Charges d'exploitation (%)", 10, 30, 17, 1) / 100

if st.sidebar.button("Lancer la simulation"):
    params = dict(
        prix_paris=prix_paris, charges_paris_0=charges_paris,
        appr_paris=appr_paris, loyer_paris_0=loyer_paris_0, inflation=inflation,
        apport_pct=10, frais_not_pct=8, taux_credit=3/100,  # constants
        horizon=horizon,
        rdt_bourse_2=rdt_bourse_2, rdt_bourse_3=rdt_bourse_3,
        prix_loc=prix_loc, rend_brut=rend_brut,
        vacance=vacance, charges_exploit=charges_expl, tax_fonc=taxe_fonciere,
        appr_loc=appr_loc
    )

    res = run_simulation(params)

    st.header("Résultats synthétiques")
    st.metric("IRR Achat Paris", f"{res['IRR_A']*100:.2f} %")
    st.metric("IRR Location + Bourse", f"{res['IRR_B']*100:.2f} %")
    st.metric("IRR Locatif + Bourse", f"{res['IRR_C']*100:.2f} %")

    col1, col2, col3 = st.columns(3)
    col1.metric("Patrimoine Achat", f"{res['patr_A']:,.0f} €")
    col2.metric("Patrimoine Bourse", f"{res['patr_B']:,.0f} €")
    col3.metric("Patrimoine Locatif", f"{res['patr_C']:,.0f} €")

    st.header("Évolution du patrimoine net")
    fig, ax = plt.subplots()
    for label, courbe in res["courbes"].items():
        ax.plot(res["temps"], courbe, label=label)
    ax.set_xlabel("Années")
    ax.set_ylabel("Patrimoine (€)")
    ax.grid(True)
    ax.legend()
    st.pyplot(fig)
