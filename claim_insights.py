
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
from datetime import datetime
from fpdf import FPDF

st.set_page_config(page_title="Reporting Réclamations", layout="wide")

st.title("📊 Reporting Réclamations")

uploaded_file = st.file_uploader("Téléverser un fichier Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # Nettoyage des dates
    df["DATE CREATION"] = pd.to_datetime(df["DATE CREATION"], errors="coerce")
    df["DATE CLOTURE"] = pd.to_datetime(df["DATE CLOTURE"], errors="coerce")
    today = pd.to_datetime("today")

    # Calcul du Délai JO
    df["Délai JO recalculé"] = (df["DATE CLOTURE"].fillna(today) - df["DATE CREATION"]).dt.days

    # Tranches de délai
    def categorize_delay(d):
        if pd.isna(d):
            return "Non défini"
        if d < 10:
            return "< 10 jours"
        elif 10 <= d <= 40:
            return "10 à 40 jours"
        else:
            return "> 40 jours"

    df["Tranche délai"] = df["Délai JO recalculé"].apply(categorize_delay)

    # Mois / Année
    df["Mois"] = df["DATE CREATION"].dt.month
    df["Année"] = df["DATE CREATION"].dt.year

    # Restitution binaire
    df["Restituée"] = df["RESTITUTION"].fillna("Non").apply(lambda x: "Oui" if str(x).strip().upper() == "OUI" else ("Non" if str(x).strip().upper() == "NON" else "Non renseigné"))
    df["Montant Restitué"] = df.apply(lambda x: x["MONTANT RESTITUTION"] if x["Restituée"] == "Oui" else 0, axis=1)

    # Filtres dynamiques
    st.sidebar.header("🔎 Filtres")

    def multiselect_with_all(label, options):
        return st.sidebar.multiselect(label, ["ALL"] + options, default=["ALL"])

    filtre_tranche = multiselect_with_all("Tranche délai", sorted(df["Tranche délai"].dropna().unique()))
    filtre_responsable = multiselect_with_all("Responsable", sorted(df["RESPONSABLE"].dropna().unique()))
    filtre_statut = multiselect_with_all("Statut", sorted(df["STATUS"].dropna().unique()))
    filtre_canal = multiselect_with_all("Canal source", sorted(df["CANAL SOURCE"].dropna().unique()))
    filtre_restitution = multiselect_with_all("Restitution", sorted(df["Restituée"].dropna().unique()))
    filtre_mois = multiselect_with_all("Mois", sorted(df["Mois"].dropna().unique()))
    filtre_annee = multiselect_with_all("Année", sorted(df["Année"].dropna().unique()))

    # Application des filtres
    def apply_filter(col, filtre):
        return df[col].isin(filtre[1:]) if "ALL" not in filtre else pd.Series([True] * len(df))

    filtre_mask = (
        apply_filter("Tranche délai", filtre_tranche) &
        apply_filter("RESPONSABLE", filtre_responsable) &
        apply_filter("STATUS", filtre_statut) &
        apply_filter("CANAL SOURCE", filtre_canal) &
        apply_filter("Restituée", filtre_restitution) &
        apply_filter("Mois", filtre_mois) &
        apply_filter("Année", filtre_annee)
    )

    df_filtré = df[filtre_mask]

    st.subheader("📌 Statistiques principales")
    col1, col2 = st.columns(2)
    col1.metric("Nombre total de réclamations", len(df_filtré))
    col2.metric("Montant total restitué", f"{df_filtré['Montant Restitué'].sum():,.0f} MAD")

    # 📊 Graphes dynamiques alternés
    st.subheader("📊 Visualisations dynamiques")
    charts = {
        "RESPONSABLE": "Histogramme",
        "FAMILLE": "Camembert",
        "ENTITE RESPONSABLE": "Histogramme",
        "STATUS": "Camembert",
        "CANAL SOURCE": "Histogramme",
        "FONDEE": "Camembert"
    }

    for var, chart_type in charts.items():
        st.markdown(f"#### {var}")
        fig, ax = plt.subplots()
        data = df_filtré[var].fillna("Non renseigné").value_counts()
        if chart_type == "Histogramme":
            sns.barplot(x=data.index, y=data.values, ax=ax)
            plt.xticks(rotation=45)
        else:
            ax.pie(data.values, labels=data.index, autopct="%1.1f%%")
        st.pyplot(fig)

    # 📅 Histogramme nombre de réclamations par jour
    st.subheader("📅 Histogramme quotidien")
    date_counts = df_filtré["DATE CREATION"].dt.date.value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(10, 4))
    sns.barplot(x=date_counts.index, y=date_counts.values, ax=ax)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45)
    st.pyplot(fig)

    # Moyenne délai par Responsable et Famille
    st.subheader("⏱ Moyenne Délai JO")
    for var in ["RESPONSABLE", "FAMILLE"]:
        st.markdown(f"##### Par {var}")
        moyennes = df_filtré.groupby(var)["Délai JO recalculé"].mean().dropna()
        fig, ax = plt.subplots()
        sns.barplot(x=moyennes.index, y=moyennes.values, ax=ax)
        ax.set_ylabel("Délai moyen (jours)")
        plt.xticks(rotation=45)
        st.pyplot(fig)

    # Génération PDF
    st.subheader("🧾 Exporter le reporting en PDF")
    if st.button("📥 Télécharger le PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Reporting Réclamations", ln=True, align="C")
        pdf.ln(10)
        pdf.cell(200, 10, txt=f"Nombre total de réclamations : {len(df_filtré)}", ln=True)
        pdf.cell(200, 10, txt=f"Montant total restitué : {df_filtré['Montant Restitué'].sum():,.0f} MAD", ln=True)
        pdf.ln(10)
        pdf.output("/mnt/data/reporting_reclamations.pdf")
        with open("/mnt/data/reporting_reclamations.pdf", "rb") as f:
            st.download_button("📄 Télécharger le fichier PDF", f, file_name="reporting_reclamations.pdf")
