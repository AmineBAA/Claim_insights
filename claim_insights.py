import streamlit as st
import pandas as pd
import datetime as dt
import io
import plotly.express as px
from fpdf import FPDF
import tempfile

# Fonction PDF
def generate_pdf_report(data_stats, file_path="report.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Rapport Réclamations - Synthèse", ln=True, align="C")
    pdf.ln(10)

    for title, value in data_stats.items():
        pdf.cell(200, 10, txt=f"{title}: {value}", ln=True)

    pdf.output(file_path)

# Chargement du fichier
st.title("📊 Reporting Réclamations Clients PDF + Graphiques")

uploaded_file = st.file_uploader("📎 Chargez un fichier Excel", type=["xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    
    # Traitement des dates
    today = pd.to_datetime(dt.datetime.today().date())
    df["DATE CREATION"] = pd.to_datetime(df["DATE CREATION"], errors="coerce")
    df["Délai JO recalculé"] = (df["DATE CLOTURE"].fillna(today) - df["DATE CREATION"]).dt.days
    
    # Statistiques pour le PDF
    total_reclamations = len(df)
    montant_total = df[df["RESTITUTION"] == "OUI"]["MONTANT RESTITUTION"].sum()

    # Choix des types de graphiques
    chart_type = st.selectbox("📈 Type de graphique à afficher", ["Histogramme", "Camembert"])
    var_to_plot = st.selectbox("📊 Variable à analyser", ["RESPONSABLE", "FAMILLE", "CANAL SOURCE", "STATUS"])

    plot_data = df[var_to_plot].fillna("Non renseigné").value_counts().nlargest(10).reset_index()
    plot_data.columns = [var_to_plot, "Nombre"]

    if chart_type == "Histogramme":
        fig = px.bar(plot_data, x=var_to_plot, y="Nombre", title=f"Histogramme des {var_to_plot}")
    else:
        fig = px.pie(plot_data, names=var_to_plot, values="Nombre", title=f"Répartition des {var_to_plot}")

    st.plotly_chart(fig, use_container_width=True)

    # Génération PDF
    if st.button("📄 Générer rapport PDF"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
            generate_pdf_report(
                {
                    "Total réclamations": total_reclamations,
                    "Montant total restitué": f"{montant_total:,.2f} MAD"
                },
                file_path=tmpfile.name
            )
            with open(tmpfile.name, "rb") as f:
                st.download_button(
                    label="📥 Télécharger le rapport PDF",
                    data=f,
                    file_name="rapport_reclamations.pdf",
                    mime="application/pdf"
                )
