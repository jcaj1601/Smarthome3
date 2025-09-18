import streamlit as st
import pandas as pd
from utils.ui import inject_css, hero, kpi, sidebar_header, card_buttons

# ==============================
# Configuración inicial
# ==============================
st.set_page_config(page_title="Smart Housing Madrid", layout="wide", page_icon="🧭")

# ==============================
# Branding lateral + CSS
# ==============================
sidebar_header()
inject_css()

# ==============================
# Encabezado principal (hero)
# ==============================
hero()

# ==============================
# Tarjetas-resumen (valores dinámicos)
# ==============================
st.markdown("## Conoce el mercado ⬇️")
try:
    df_sum = pd.read_csv("data/district_features.csv")
    # Calcular métricas: precio medio de la ciudad y variación media
    precio_ciudad_val = df_sum["PRECIO_EUR_M2"].mean()
    variacion_media = df_sum["VARIACION_PCT"].mean()
    # Distrito más caro y más barato
    df_sum["distrito_nombre"] = df_sum["DISTRITO"].str.split(".").str[-1].str.strip()
    distrito_caro_val = df_sum.loc[df_sum["PRECIO_EUR_M2"].idxmax(), "distrito_nombre"]
    distrito_barato_val = df_sum.loc[df_sum["PRECIO_EUR_M2"].idxmin(), "distrito_nombre"]
    precio_ciudad = f"{precio_ciudad_val:,.0f}"
    variacion = f"{variacion_media:.1f}%"
    distrito_caro = distrito_caro_val
    distrito_barato = distrito_barato_val
except Exception:
    # Valores de reserva si falla la carga
    precio_ciudad = "--"
    variacion = "--"
    distrito_caro = "--"
    distrito_barato = "--"
card_buttons(precio_ciudad, distrito_caro, distrito_barato, variacion)

st.markdown("---")

# ==============================
# Helper de navegación
# ==============================
def go(page_path: str, objetivo: str | None = None):
    """
    Navega a una página multipage y opcionalmente marca 'objetivo'
    para personalizar el hero y/o el flujo.
    """
    if objetivo:
        st.session_state["objetivo"] = objetivo
    st.switch_page(page_path)

# ==============================
# CTAs principales (flujo natural)
# ==============================
st.subheader("¿Qué quieres hacer hoy?")
cta = st.columns(3)

with cta[0]:
    if st.button("🧭 Asistente guiado", use_container_width=True):
        # El asistente define por defecto 'comprar' si no hay objetivo en sesión
        go("pages/1_Asistente.py", objetivo=None)

with cta[1]:
    if st.button("🧮 Calculadora", use_container_width=True):
        go("pages/3_Calculadora.py")

with cta[2]:
    if st.button("🔬 Análisis avanzado", use_container_width=True):
        go("pages/4_Modo_Avanzado.py")

# ==============================
# Pie de página académico
# ==============================
st.caption(
    """
    <div style="text-align: center;">
        TFM: Modelado del precio de la vivienda en Madrid: enfoque multidimensional basado en técnicas de Big Data y Machine Learning (2015–2024).
        <br><br>
        Máster Data Science, Big Data & Business Analytics 2024-2025.
        <br><br>
        UCM.
    </div>
    """,
    unsafe_allow_html=True
)
