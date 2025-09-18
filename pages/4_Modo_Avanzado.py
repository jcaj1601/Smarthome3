import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils.ui import inject_css

# ==============================
# Configuración inicial
# ==============================
st.set_page_config(page_title="Análisis avanzado", layout="wide", page_icon="🧭")
inject_css()
st.title("🔬 Análisis avanzado del mercado")

# ==============================
# Cargar datos agregados de distrito
# ==============================
# Utilizamos el CSV con los indicadores agregados por distrito para los análisis
df = pd.read_csv("data/district_features.csv")

st.caption(
    "🗂️ Dataset de indicadores agregados por distrito. Columnas como `PRECIO_EUR_M2`, `RENTA_NETA_PERSONA`, `PARADAS_METRO`, etc."
)

# Renombrar columnas clave para visualización sencilla
df_ren = df.rename(columns={"PRECIO_EUR_M2": "precio_m2", "VARIACION_PCT": "variacion_pct"})

# ==============================
# Tabs de análisis
# ==============================
tab1, tab2, tab3 = st.tabs([
    "📊 Correlaciones",
    "⭐ Correlación con €/m²",
    "📥 Descarga de datos"
])

# --- TAB 1: Correlaciones entre variables numéricas ---
with tab1:
    st.subheader("Matriz de correlación (variables numéricas)")
    # Seleccionar columnas numéricas con al menos alguna variación
    num_cols = [c for c in df_ren.select_dtypes(include=[np.number]).columns if c not in {"precio_m2", "variacion_pct"}]
    # Añadimos precio y variacion si existen
    heat_df = df_ren[num_cols + ["precio_m2", "variacion_pct"]].copy()
    corr = heat_df.corr()
    heatmap = go.Figure(data=go.Heatmap(
        z=corr.values,
        x=corr.columns,
        y=corr.index,
        colorscale='Blues',
        zmin=-1,
        zmax=1,
        colorbar=dict(title="Correlación")
    ))
    heatmap.update_layout(title="Matriz de correlaciones")
    st.plotly_chart(heatmap, use_container_width=True)

    st.subheader("Relación €/m² vs variación porcentual")
    fig_scatter = px.scatter(
        df_ren, x="precio_m2", y="variacion_pct",
        text=df_ren["DISTRITO"].str.split(".").str[-1],
        title="Relación precio medio €/m² vs variación porcentual",
        labels={"precio_m2": "€/m²", "variacion_pct": "Variación (%)"},
        color="variacion_pct", color_continuous_scale="RdYlGn"
    )
    fig_scatter.update_traces(textposition='top center')
    st.plotly_chart(fig_scatter, use_container_width=True)

# --- TAB 2: Correlación de características con el precio ---
with tab2:
    st.subheader("Características con mayor correlación con el precio €/m²")
    # Calcular la correlación absoluta de cada variable numérica con el precio
    corr_with_price = df_ren.corr()["precio_m2"].drop("precio_m2").dropna()
    corr_abs = corr_with_price.abs().sort_values(ascending=False)
    top_corr = corr_abs.head(10)
    fig_importance = px.bar(
        x=top_corr.values[::-1],
        y=[col for col in top_corr.index[::-1]],
        orientation="h",
        title="Top variables correlacionadas con €/m²"
    )
    st.plotly_chart(fig_importance, use_container_width=True)
    st.info("Estas correlaciones indican la relación lineal entre cada variable y el precio promedio €/m². El valor absoluto muestra la fuerza de la relación.")

# --- TAB 3: Descargas ---
with tab3:
    st.subheader("Descargar datos de distrito")
    st.write("Puedes descargar el CSV con todas las variables agregadas por distrito para tu propio análisis.")
    # Mostrar una vista previa del DataFrame
    st.dataframe(df_ren.head(20), use_container_width=True)
    st.download_button(
        "📥 Descargar CSV",
        data=df_ren.to_csv(index=False).encode(),
        file_name="district_features.csv"
    )
