# (Suite de l'interface Streamlit)
    appr_loc = st.number_input("Appréciation locatif (%)", 0.0, 3.0, 1.0, 0.1)
    vacance = st.slider("Vacance locative (mois/an)", 0, 6, 1, 1) / 12
    charges_expl = st.slider("Charges d'exploitation (%)", 10, 30, 17, 1) / 100
    taxe_fonciere = st.number_input("Taxe foncière annuelle (€)", 0, 5_000, 1_000, 50)

if st.sidebar.button("Lancer la simulation"):
    params = dict(
        prix_paris=prix_paris,
        charges_paris_0=charges_paris,
        appr_paris=appr_paris,
        loyer_paris_0=loyer_paris_0,
        inflation=inflation,
        apport_pct=10,
        frais_not_pct=8,
        taux_credit=0.03,
        horizon=horizon,
        rdt_bourse_2=rdt_bourse_2,
        rdt_bourse_3=rdt_bourse_3,
        prix_loc=prix_loc,
        rend_brut=rend_brut,
        vacance=vacance,
        charges_exploit=charges_expl,
        taxe_fonc=taxe_fonciere,
        appr_loc=appr_loc,
    )

    res = run_simulation(params)

    st.header("Résultats synthétiques")
    st.metric("IRR Achat Paris", f"{res['IRR_A'] * 100:.2f} %")
    st.metric("IRR Location + Bourse", f"{res['IRR_B'] * 100:.2f} %")
    st.metric("IRR Locatif + Bourse", f"{res['IRR_C'] * 100:.2f} %")

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

    st.header("Cumul des sorties d'argent par an")
    fig2, ax2 = plt.subplots()
    annees = list(range(horizon + 1))
    for label, courbe in res["cum_out"].items():
        ax2.plot(annees, courbe, label=label)
    ax2.set_xlabel("Années")
    ax2.set_ylabel("Cumul des sorties (€)")
    ax2.grid(True)
    ax2.legend()
    st.pyplot(fig2)
