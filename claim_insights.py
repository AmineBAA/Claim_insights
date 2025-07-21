
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import numpy as np
from io import BytesIO

st.set_page_config(page_title="Dashboard Réclamations", layout="wide")
st.image("logo_saham.png", use_container_width=False)
st.title("📊 Dashboard Réclamations - Version Propre")

uploaded_file = st.file_uploader("📎 Téléversez un fichier Excel", type=["xlsx"])

def business_days_between(start_date, end_date):
    return np.busday_count(start_date.date(), end_date.date())

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df["DATE CREATION"] = pd.to_datetime(df["DATE CREATION"], errors="coerce")
    df["DATE CLOTURE"] = pd.to_datetime(df["DATE CLOTURE"], errors="coerce")
    today = pd.to_datetime("today")

    df["delai_recalcule"] = df.apply(
        lambda row: business_days_between(row["DATE CREATION"], row["DATE CLOTURE"]) if pd.notnull(row["DATE CLOTURE"])
        else business_days_between(row["DATE CREATION"], today),
        axis=1
    )

    df["ETAT"] = df["DATE CLOTURE"].apply(lambda x: "Clôturée" if pd.notnull(x) else "En cours")

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

    st.sidebar.header("🔎 Filtres")

    categorie_filter = st.sidebar.multiselect("Catégorie de délai", option=df["delai_Categ"].unique() )
    seuil_max = st.sidebar.slider("Délai maximum (jours ouvrés)", int(df["delai_recalcule"].min()), int(df["delai_recalcule"].max()), int(df["delai_recalcule"].max()))
    status_filter = st.sidebar.multiselect("Statut", df["STATUS"].dropna().unique(), default=df["STATUS"].dropna().unique())

    df_filtered = df[
    (df["delai_Categ"].isin(categorie_filter)) &
    (df["delai_recalcule"] <= seuil_max) &
    (df["STATUS"].isin(status_filter))
     ]


    st.subheader("📌 Statistiques principales")
    col1, col2 = st.columns(2)
    col1.metric("Nombre total de réclamations", len(df_filtered))
    col2.metric("Réclamations avec délai ≥ 40 jours", df_filtered[df_filtered["delai_recalcule"] >= 40].shape[0])

    # Figures
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

    top_fam = df_filtered["FAMILLE"].value_counts().nlargest(4)
    df_filtered["famille_grouped"] = df_filtered["FAMILLE"].apply(lambda x: x if x in top_fam.index else "Autre")
    famille_pct = df_filtered["famille_grouped"].value_counts(normalize=True)
    fig2, ax2 = plt.subplots()
    ax2.pie(famille_pct, labels=famille_pct.index, autopct="%1.1f%%", startangle=90)

    now = pd.to_datetime("today")
    df_mois = df_filtered[df_filtered["DATE CREATION"].dt.month == now.month]
    day_counts = df_mois["DATE CREATION"].dt.day.value_counts().sort_index()
    fig3, ax3 = plt.subplots()
    sns.barplot(x=day_counts.index, y=day_counts.values, ax=ax3)
    ax3.set_xlabel("Jour du mois")
    ax3.set_ylabel("Réclamations")

    etat_count = df_filtered["ETAT"].value_counts()
    fig4, ax4 = plt.subplots()
    sns.barplot(x=etat_count.index, y=etat_count.values, ax=ax4)
    ax4.set_ylabel("Nombre")

    st.subheader("📊 Visualisations")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Par catégorie de délai**")
        st.pyplot(fig1)
    with col2:
        st.markdown("**Par famille (4 principales)**")
        st.pyplot(fig2)

    col3, col4 = st.columns(2)
    with col3:
        st.markdown("**Par jour du mois courant**")
        st.pyplot(fig3)
    with col4:
        st.markdown("**Répartition par état**")
        st.pyplot(fig4)

    st.subheader("📋 Données filtrées")
    st.dataframe(df_filtered)

    output = BytesIO()
    df_filtered.to_excel(output, index=False, engine='openpyxl')
    st.download_button("📥 Exporter en Excel", data=output.getvalue(), file_name="reclamations_filtrees.xlsx")
