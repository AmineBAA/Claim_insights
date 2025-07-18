import streamlit as st
import pandas as pd
import datetime as dt
import io

st.set_page_config(page_title="Reporting Réclamations", layout="wide")
st.title("📊 Reporting Réclamations Clients")

uploaded_file = st.file_uploader("📎 Téléversez le fichier Excel des réclamations", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # Nettoyage des dates
    today = pd.to_datetime(dt.datetime.today().date())
    df["DATE CREATION"] = pd.to_datetime(df["DATE CREATION"], errors='coerce')
    df["DATE CLOTURE"] = pd.to_datetime(df["DATE CLOTURE"], errors='coerce')

    # Délai JO recalculé
    df["Délai JO recalculé"] = (df["DATE CLOTURE"].fillna(today) - df["DATE CREATION"]).dt.days

    # Tranche délai
    def categorize_delay(d):
        if pd.isna(d):
            return "Non défini"
        elif d < 10:
            return "< 10 jours"
        elif 10 <= d <= 40:
            return "10 à 40 jours"
        else:
            return "> 40 jours"

    df["Tranche délai"] = df["Délai JO recalculé"].apply(categorize_delay)

    # Restitution
    def rest_label(val):
        if pd.isna(val) or str(val).strip() == "":
            return "Non renseigné"
        val = str(val).strip().upper()
        return "OUI" if val == "OUI" else "NON"

    df["Restitution label"] = df["RESTITUTION"].apply(rest_label)
    df["Montant Restitué"] = df.apply(
        lambda x: x["MONTANT RESTITUTION"] if x["Restitution label"] == "OUI" else 0, axis=1)

    # Mois / Année de création
    df["Année"] = df["DATE CREATION"].dt.year.fillna("Non renseigné")
    df["Mois"] = df["DATE CREATION"].dt.month.fillna("Non renseigné")

    # Remplacer les valeurs NaN pour les filtres
    df["RESPONSABLE"] = df["RESPONSABLE"].fillna("Non renseigné")
    df["STATUS"] = df["STATUS"].fillna("Non renseigné")
    df["CANAL SOURCE"] = df["CANAL SOURCE"].fillna("Non renseigné")
    df["FAMILLE"] = df["FAMILLE"].fillna("Non renseigné")
    df["ENTITE RESPONSABLE"] = df["ENTITE RESPONSABLE"].fillna("Non renseigné")
    df["FONDEE"] = df["FONDEE"].fillna("Non renseigné")

    # --- 🔍 Filtres ---
    st.sidebar.header("🔎 Filtres")

    tranche_options = sorted(df["Tranche délai"].unique())
    responsable_options = sorted(df["RESPONSABLE"].unique())
    statut_options = sorted(df["STATUS"].unique())
    canal_options = sorted(df["CANAL SOURCE"].unique())
    restitution_options = sorted(df["Restitution label"].unique())
    annees = sorted(df["Année"].unique())
    mois = sorted(df["Mois"].unique())

    tranche_filtre = st.sidebar.multiselect("Tranche délai", tranche_options, default=tranche_options)
    responsable_filtre = st.sidebar.multiselect("Responsable", responsable_options, default=responsable_options)
    statut_filtre = st.sidebar.multiselect("Statut", statut_options, default=statut_options)
    canal_filtre = st.sidebar.multiselect("Canal source", canal_options, default=canal_options)
    restitution_filtre = st.sidebar.multiselect("Restitution", restitution_options, default=restitution_options)
    annee_filtre = st.sidebar.multiselect("Année", annees, default=annees)
    mois_filtre = st.sidebar.multiselect("Mois", mois, default=mois)

    # --- 🎯 Application des filtres ---
    df_filtered = df[
        df["Tranche délai"].isin(tranche_filtre) &
        df["RESPONSABLE"].isin(responsable_filtre) &
        df["STATUS"].isin(statut_filtre) &
        df["CANAL SOURCE"].isin(canal_filtre) &
        df["Restitution label"].isin(restitution_filtre) &
        df["Année"].isin(annee_filtre) &
        df["Mois"].isin(mois_filtre)
    ]

    # --- 📊 Visualisations ---
    st.subheader("📅 Histogramme des réclamations par jour")
    by_day = df_filtered["DATE CREATION"].dt.date.value_counts().sort_index()
    st.bar_chart(by_day)

    st.subheader("📌 Répartition par Tranche de Délai")
    st.bar_chart(df_filtered["Tranche délai"].value_counts())

    st.subheader("💰 Montant total restitué")
    st.metric("Total", f"{df_filtered['Montant Restitué'].sum():,.2f} MAD")

    st.subheader("👤 Réclamations par Responsable")
    st.bar_chart(df_filtered["RESPONSABLE"].value_counts())

    st.subheader("🏢 Réclamations par Entité Responsable")
    st.bar_chart(df_filtered["ENTITE RESPONSABLE"].value_counts())

    st.subheader("🏷️ Réclamations par Famille")
    st.bar_chart(df_filtered["FAMILLE"].value_counts())

    st.subheader("⚖️ Réclamations Fondées vs Non Fondées")
    st.bar_chart(df_filtered["FONDEE"].value_counts())

    st.subheader("📡 Réclamations par Canal Source")
    st.bar_chart(df_filtered["CANAL SOURCE"].value_counts())

    # --- 📥 Téléchargement fichier enrichi filtré ---
    st.subheader("📥 Télécharger le fichier enrichi filtré")
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df_filtered.to_excel(writer, index=False, sheet_name="Réclamations filtrées")
        writer.save()
        st.download_button("📁 Télécharger Excel", data=buffer.getvalue(),
                           file_name="Reclamations_filtrees.xlsx", mime="application/vnd.ms-excel")
