import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils.ui import inject_css, chip

# ==============================
# Configuración inicial
# ==============================
st.set_page_config(page_title="Asistente", layout="wide", page_icon="🧭")
inject_css()
st.title("")
st.title("Asistente: Encuentra tu mejor lugar y momento")

# ==============================
# Helpers
# ==============================
def semaforo_color(valor: float) -> tuple[str, str]:
    """
    Devuelve (color_hex, emoji) según variación interanual.
    > 2%: verde, ~ estable: amarillo, < -0.3%: rojo
    """
    if valor > 2:
        return "#3FA34D", "🟢"
    elif valor > -0.3:
        return "#E1A500", "🟡"
    return "#AA1927", "🔴"

def tarjetas_recomendacion(df_top: pd.DataFrame):
    cols = st.columns(len(df_top))
    for i, (_, row) in enumerate(df_top.iterrows()):
        color, emoji = semaforo_color(float(row["variacion_interanual"]))
        with cols[i]:
            st.markdown(
                f"""
                <div style="border:1px solid #e5e7eb;border-radius:12px;padding:14px;text-align:center;background:#fff">
                    <div style="font-weight:800;font-size:1.05rem">{emoji} {row['distrito']}</div>
                    <div style="margin-top:6px;font-size:1.1rem"><b>{int(row['precio_m2']):,} €/m²</b></div>
                    <div style="margin-top:4px;color:{color}">{row['variacion_interanual']}% tendencia</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            # Microserie demo
            y = np.cumsum(np.random.randn(24)) * 5 + row["precio_m2"]
            fig = px.line(x=list(range(24)), y=y, labels={"x": "meses", "y": "€/m²"})
            fig.update_layout(height=120, margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig, use_container_width=True)

def proyeccion_demo(base: float, titulo: str):
    meses = np.arange(0, 24)
    trend = base * (1 + 0.002 * meses)  # demo
    noise = np.linspace(-80, 80, 24)
    p50 = trend + noise
    p10, p90 = p50 - 150, p50 + 150

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=meses, y=p90, mode="lines", name="P90", line=dict(width=1)))
    fig.add_trace(go.Scatter(x=meses, y=p10, mode="lines", name="P10", line=dict(width=1), fill=None))
    fig.add_trace(go.Scatter(
        x=np.concatenate([meses, meses[::-1]]),
        y=np.concatenate([p90, p10[::-1]]),
        fill="toself", name="Banda P10–P90", opacity=0.15, line=dict(width=0)
    ))
    fig.add_trace(go.Scatter(x=meses, y=p50, mode="lines", name="P50", line=dict(width=2)))
    fig.update_layout(title=titulo, xaxis_title="Meses", yaxis_title="€/m²", height=380, margin=dict(l=0,r=0,t=40,b=0))
    st.plotly_chart(fig, use_container_width=True)

# ==============================
# Selección de objetivo (persistente)
# ==============================
st.markdown("### ¿Cuál es tu objetivo?")
objetivo = st.radio(
    "Selecciona una opción:",
    ["comprar", "vender", "explorar"],
    horizontal=True,
    index=["comprar", "vender", "explorar"].index(st.session_state.get("objetivo", "comprar"))
)
st.session_state["objetivo"] = objetivo
st.write(f"**Has elegido:** {objetivo.capitalize()}")

# ==============================
# Cargar datos de distritos (agregados)
# ==============================
# Cargamos el dataset de características por distrito generado a partir de la base MASTER_BD_VIVIENDA_2015a2024.xlsx.
# Este archivo contiene la media de las variables relevantes por distrito y la variación porcentual del precio
# entre los extremos del periodo 2015–2024.
df = pd.read_csv("data/district_features.csv")

# Normalizamos nombres de columna para trabajar en minúsculas y crear etiquetas más amigables
df = df.rename(columns={
    "DISTRITO": "distrito",
    "PRECIO_EUR_M2": "precio_m2",
    "VARIACION_PCT": "variacion_pct"
})

# Extraemos un nombre corto de distrito eliminando el prefijo numérico ("01. Centro" -> "Centro")
df["distrito_nombre"] = df["distrito"].str.split(".").str[-1].str.strip()

# Calculamos una columna de puntuación para recomendaciones de compra:
df["score"] = df["variacion_pct"].rank(ascending=False) + df["precio_m2"].rank(ascending=True)

# Para compatibilidad con funciones anteriores, creamos variacion_interanual como la variación porcentual
df["variacion_interanual"] = df["variacion_pct"]

# ==============================
# Paso 1: Perfilado inicial (dinámico)
# ==============================
with st.expander("① Perfilado inicial", expanded=True):
    c1, c2 = st.columns([2, 1])

    if objetivo == "comprar":
        with c1:
            presupuesto = st.slider("Presupuesto máximo (€)", 120_000, 1_200_000, 350_000, 10_000)
            habitaciones = st.selectbox("Habitaciones", [1, 2, 3, 4], index=1)
            prioridades = st.multiselect(
                "Prioridades", ["Precio bajo", "Zonas verdes", "Transporte", "Seguridad", "Inversión"],
                default=["Precio bajo", "Transporte"]
            )
            st.write("**Tus prioridades:**")
            for p in prioridades: chip(p)
        with c2:
            st.info("Te recomendaremos distritos en función de tu presupuesto y prioridades.")

    elif objetivo == "vender":
        with c1:
            # Permitimos seleccionar el distrito a partir del nombre sin prefijo numérico
            distrito_v = st.selectbox(
                "¿En qué distrito está tu vivienda?",
                options=df["distrito_nombre"].unique().tolist()
            )
            # Inputs adicionales (demo) que en producción podrían alimentar un modelo más detallado
            superficie = st.number_input("Superficie (m²)", 20, 400, 85)
            antiguedad = st.slider("Antigüedad (años)", 0, 120, 35)
            ascensor = st.selectbox("Ascensor", ["Sí", "No"], index=0)
        with c2:
            st.info("Analizaremos el mercado de tu zona y te diremos si es buen momento para vender.")

    else:  # explorar
        with c1:
            criterios = st.multiselect(
                "¿Qué quieres explorar?",
                ["Distritos más caros", "Distritos más baratos", "Mayor crecimiento", "Mejor relación €/m² vs renta"],
                default=["Mayor crecimiento"]
            )
            st.write("**Criterios seleccionados:**")
            for c in criterios: chip(c)
        with c2:
            st.info("Explora el mercado por criterios y compara zonas en un clic.")


# ==============================
# Paso 2: Recomendaciones / Análisis inicial (condicional)
# ==============================
st.markdown("---")

if objetivo == "comprar":
    st.subheader("② Recomendaciones de compra")
    # Ranking de distritos basados en precio medio y variación porcentual.
    df_top = df.sort_values("score").head(3)
    tarjetas_recomendacion(df_top)

elif objetivo == "vender":
    st.subheader("② Análisis de tu distrito")
    # Seleccionamos la fila correspondiente al distrito elegido (por nombre corto)
    distrito_sel = locals().get("distrito_v", df["distrito_nombre"].iloc[0])
    row = df.loc[df["distrito_nombre"] == distrito_sel].head(1)
    if row.empty:
        st.warning("No hay datos para el distrito seleccionado; usando valores de demo.")
        precio_base, variacion = 4000.0, 0.0
    else:
        precio_base = float(row["precio_m2"].values[0])
        variacion = float(row["variacion_pct"].values[0])
    color, emoji = semaforo_color(variacion)
    st.metric(label=f"Precio medio en {distrito_sel}", value=f"{precio_base:,.0f} €/m²", delta=f"{variacion:.2f}%")
    st.info(f"{emoji} Estado del mercado en {distrito_sel} — "
            + ("alza: buen momento para vender." if emoji=="🟢" else "estable." if emoji=="🟡" else "a la baja: quizá conviene esperar."))

else:  # explorar
    st.subheader("② Distritos destacados")
    # Top 6 distritos por precio medio con color según variación porcentual
    df_sorted = df.sort_values("precio_m2", ascending=False).head(6)
    fig_bar = px.bar(df_sorted, x="distrito_nombre", y="precio_m2", color="variacion_pct",
                     title="Top distritos por €/m² (color por variación %)",
                     color_continuous_scale="RdYlGn")
    st.plotly_chart(fig_bar, use_container_width=True)
    st.caption("Escala de color: verde=crece, amarillo=estable, rojo=cae.")

# ==============================
# Paso 3: Comparador integrado (siempre visible, contextual)
# ==============================
st.markdown("---")
st.subheader("③ Comparar distritos")

# Sugerencias por defecto según objetivo
if objetivo == "comprar":
    sugeridos = df.sort_values("score").head(3)["distrito_nombre"].tolist() if "score" in df.columns else df["distrito_nombre"].head(3).tolist()
elif objetivo == "vender":
    # sugerimos el mismo distrito seleccionado en el perfilado
    sugeridos = [locals().get("distrito_v", df["distrito_nombre"].iloc[0])]
else:
    sugeridos = df.sort_values("precio_m2", ascending=False).head(3)["distrito_nombre"].tolist()


seleccion = st.multiselect(
    "Selecciona uno o más distritos para comparar",
    options=df["distrito_nombre"].tolist(),
    default=sugeridos
)

if seleccion:
    df_sel = df[df["distrito_nombre"].isin(seleccion)].copy()
    # Tabla comparativa con semáforo textual
    df_sel["semaforo"] = df_sel["variacion_pct"].apply(
        lambda v: "🟢" if v > 2 else ("🟡" if v > -0.3 else "🔴")
    )
    st.dataframe(
        df_sel[["distrito_nombre","precio_m2","variacion_pct","semaforo"]]
        .rename(columns={"distrito_nombre":"Distrito","precio_m2":"€/m²","variacion_pct":"Variación %"}),
        use_container_width=True
    )

    # Barras €/m² con color por variación
    fig_comp = px.bar(df_sel, x="distrito_nombre", y="precio_m2", color="variacion_pct",
                      title="Comparativa €/m² (color por variación %)", color_continuous_scale="RdYlGn")
    st.plotly_chart(fig_comp, use_container_width=True)
else:
    st.info("Selecciona al menos un distrito para comparar.")

# ==============================
# Paso 4: Proyección + salto a Calculadora
# ==============================
st.markdown("---")
st.subheader("④ Momento ideal y proyección")

# Distrito preseleccionado: prioridad al flujo del objetivo
if objetivo == "comprar":
    base_df = df.sort_values("score") if "score" in df.columns else df.copy()
    default_distrito = base_df["distrito"].iloc[0]
elif objetivo == "vender":
    default_distrito = locals().get("distrito_v", df["distrito"].iloc[0])
else:
    default_distrito = seleccion[0] if seleccion else df["distrito"].iloc[0]

sel = st.selectbox("Ver proyección para:", df["distrito"].tolist(),
                   index=df["distrito"].tolist().index(default_distrito) if default_distrito in df["distrito"].tolist() else 0)

base_precio = float(df.loc[df["distrito"]==sel,"precio_m2"].iloc[0]) if sel in df["distrito"].values else 4000.0
proyeccion_demo(base_precio, f"Proyección en {sel} (P10–P90 • demo)")
st.info("Intervalos de confianza ( % 10, % 50, % 90).")

c1, c2 = st.columns(2)
with c1:
    if st.button("🔮 Proyectar en Calculadora Personalizada", use_container_width=True):
        # Prefill para Calculadora
        st.session_state["selected_distrito"] = sel
        if objetivo == "vender":
            st.session_state["calc_superficie"] = locals().get("superficie", 85)
            st.session_state["calc_antiguedad"] = locals().get("antiguedad", 35)
            st.session_state["calc_ascensor"] = 1 if locals().get("ascensor","Sí") == "Sí" else 0
        st.switch_page("pages/3_Calculadora.py")

with c2:
    st.download_button(
        "📥 Descargar resumen (CSV)",
        data=df.to_csv(index=False).encode(),
        file_name="resumen_asistente.csv",
        use_container_width=True
    )
