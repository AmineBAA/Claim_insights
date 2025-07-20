
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import numpy as np
from io import BytesIO

st.set_page_config(page_title="Reporting Réclamations Avancé", layout="wide")

# 📷 Image en haut de page
st.image("logo_saham.png", use_container_width=False)  # image en haut de page

st.title("📊 Reporting Réclamations - Version Avancée")

uploaded_file = st.file_uploader("📎 Téléverser un fichier Excel", type=["xlsx"])

def business_days_between(start_date, end_date):
    return np.busday_count(start_date.date(), end_date.date())

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    df["DATE CREATION"] = pd.to_datetime(df["DATE CREATION"], errors="coerce")
    df["DATE CLOTURE"] = pd.to_datetime(df["DATE CLOTURE"], errors="coerce")
    today = pd.to_datetime("today")

    # Délai recalculé en jours ouvrés
    df["delai_recalcule"] = df.apply(
        lambda row: business_days_between(row["DATE CREATION"], row["DATE CLOTURE"]) if pd.notnull(row["DATE CLOTURE"])
        else business_days_between(row["DATE CREATION"], today),
        axis=1
    )

    # Catégorisation du délai recalculé
    def categorize_delay(d):
        if d < 10:
            return "< 10 jours"
        elif 10 <= d < 20:
            return "10-20 jours"
        elif 20 <= d < 40:
            return "20-40 jours"
        else:
            return "> 40 jours"

    df["delai_Categ"] = df["delai_recalcule"].apply(categorize_delay)

    # Filtres dans la sidebar
    st.sidebar.header("🔎 Filtres")

    categorie_filter = st.sidebar.multiselect("Catégorie de délai", df["delai_Categ"].unique(), default=df["delai_Categ"].unique())

    seuil_max = st.sidebar.slider(
        "Délai maximum (jours ouvrés)",
        int(df["delai_recalcule"].min()),
        int(df["delai_recalcule"].max()),
        int(df["delai_recalcule"].max())
    )

    df_filtered = df[
        df["delai_Categ"].isin(categorie_filter) &
        (df["delai_recalcule"] <= seuil_max)
    ]

    # Statistiques principales
    st.subheader("📌 Statistiques principales")
    col1, col2 = st.columns(2)
    col1.metric("Nombre total de réclamations", len(df_filtered))
    col2.metric("Réclamations avec délai ≥ 40 jours", df_filtered[df_filtered["delai_recalcule"] >= 40].shape[0])

    # Répartition par catégorie de délai (camembert)
    st.subheader("🎯 Répartition par catégorie de délai (camembert)")
    colors = {
        "< 10 jours": "green",
        "10-20 jours": "orange",
        "20-40 jours": "red",
        "> 40 jours": "gray"
    }
    delay_counts = df_filtered["delai_Categ"].value_counts()
    fig1, ax1 = plt.subplots()
    ax1.pie(delay_counts, labels=delay_counts.index, colors=[colors.get(k, "blue") for k in delay_counts.index],
            autopct="%1.1f%%", startangle=90)
    st.pyplot(fig1)

    # Répartition par famille (4 principales + Autres)
    st.subheader("🏷 Répartition par famille (4 principales + Autre)")
    top_families = df_filtered["FAMILLE"].value_counts().nlargest(4)
    df_filtered["famille_grouped"] = df_filtered["FAMILLE"].apply(
        lambda x: x if x in top_families.index else "Autre"
    )
    famille_pct = df_filtered["famille_grouped"].value_counts(normalize=True)
    fig2, ax2 = plt.subplots()
    ax2.pie(famille_pct, labels=famille_pct.index, autopct="%1.1f%%", startangle=90)
    st.pyplot(fig2)

    # Réclamations par jour du mois courant
    st.subheader("📆 Réclamations par jour du mois courant")
    now = pd.to_datetime("today")
    current_month = df_filtered[df_filtered["DATE CREATION"].dt.month == now.month]
    day_counts = current_month["DATE CREATION"].dt.day.value_counts().sort_index()
    fig3, ax3 = plt.subplots()
    sns.barplot(x=day_counts.index, y=day_counts.values, ax=ax3)
    ax3.set_xlabel("Jour du mois")
    ax3.set_ylabel("Nombre de réclamations")
    st.pyplot(fig3)

    # Tableau et export
    st.subheader("📋 Données filtrées")
    st.dataframe(df_filtered)

    output = BytesIO()
    df_filtered.to_excel(output, index=False, engine='xlsxwriter')
    st.download_button("📥 Exporter en Excel", data=output.getvalue(), file_name="reclamations_filtrees.xlsx")
