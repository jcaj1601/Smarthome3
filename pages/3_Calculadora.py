import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import joblib, json, os
from utils.ui import inject_css

# ==============================
# Configuración inicial
# ==============================
st.set_page_config(page_title="Calculadora", layout="wide", page_icon="🧭")
inject_css()
st.title("🧮 Calculadora de precio")

# ==============================
# Cargar datos agregados por distrito
# ==============================
# Usamos district_features.csv para extraer valores medios de las variables utilizadas por el modelo
district_df = pd.read_csv("data/district_features.csv")
district_df = district_df.rename(columns={"DISTRITO": "distrito", "PRECIO_EUR_M2": "precio_m2"})
# Extraemos nombre corto del distrito para el desplegable
district_df["distrito_nombre"] = district_df["distrito"].str.split(".").str[-1].str.strip()

DIST_LIST = district_df["distrito_nombre"].tolist()

# ==============================
# Prefill desde Asistente (si existe)
# ==============================
default_distrito = st.session_state.get("selected_distrito", "Centro")
default_superficie = st.session_state.get("calc_superficie", 85)
default_antiguedad = st.session_state.get("calc_antiguedad", 35)
default_ascensor = st.session_state.get("calc_ascensor", 1)  # 1=Sí, 0=No

# ==============================
# Inputs
# ==============================
c1, c2, c3 = st.columns(3)
with c1:
    distrito = st.selectbox("Distrito", DIST_LIST, index=DIST_LIST.index(default_distrito))
    superficie = st.number_input("Superficie (m²)", 20, 400, int(default_superficie))
with c2:
    habitaciones = st.selectbox("Habitaciones", [1,2,3,4], index=1)
    ascensor = st.selectbox("Ascensor", ["Sí","No"], index=0 if default_ascensor==1 else 1)
with c3:
    cerca_metro = st.selectbox("Cercanía a Metro", ["Sí","No"], index=0)
    antiguedad = st.slider("Antigüedad (años)", 0, 120, int(default_antiguedad))

# ==============================
# Carga modelos y columnas de características
# ==============================
# Cargamos los modelos de cuantiles entrenados con los datos agregados por distrito.
@st.cache_resource(show_spinner=False)
def load_models():
    """
    Carga los artefactos de los modelos (P10, P50, P90) y la lista de columnas de características.
    Devuelve una tupla (feature_columns, model_p10, model_p50, model_p90, shap_explainer opcional).
    """
    models_dir = "models"
    # Cargar columnas de características
    with open(os.path.join(models_dir, 'feature_columns.json'), 'r') as f:
        feature_cols = json.load(f)
    # Cargar modelos cuantílicos
    model_p10 = joblib.load(os.path.join(models_dir, 'model_p10.pkl'))
    model_p50 = joblib.load(os.path.join(models_dir, 'model_p50.pkl'))
    model_p90 = joblib.load(os.path.join(models_dir, 'model_p90.pkl'))
    # Cargar explainer SHAP si existe
    shap_explainer = None
    shap_path = os.path.join(models_dir, 'shap_explainer.pkl')
    if os.path.exists(shap_path):
        try:
            shap_explainer = joblib.load(shap_path)
        except Exception:
            shap_explainer = None
    return feature_cols, model_p10, model_p50, model_p90, shap_explainer


feature_cols, model_p10, model_p50, model_p90, shap_explainer = load_models()

# ==============================
# Botón de cálculo real
# ==============================
if st.button("Calcular Intervalos de Confianza", use_container_width=True):
    # Seleccionar fila del distrito elegido
    row = district_df[district_df["distrito_nombre"] == distrito]
    if row.empty:
        st.error("No se encontraron datos para el distrito seleccionado.")
    else:
        # Utilizar las columnas de características esperadas por el modelo
        # Convertir a DataFrame con una fila siguiendo el orden de feature_cols
        X_input = row.copy()
        # Asegurar que las columnas estén en el orden requerido
        # Algunas columnas pueden faltar si no estaban en feature_cols; las añadimos como NaN
        for col in feature_cols:
            if col not in X_input.columns:
                X_input[col] = np.nan
        X_input = X_input[feature_cols]
        # Predecir precio €/m2 para cada cuantil
        pred_p10 = float(model_p10.predict(X_input)[0])
        pred_p50 = float(model_p50.predict(X_input)[0])
        pred_p90 = float(model_p90.predict(X_input)[0])

        # Calcular valor total según superficie
        total_p10 = pred_p10 * superficie
        total_p50 = pred_p50 * superficie
        total_p90 = pred_p90 * superficie

        # Mostrar resultados en €/m2 y valor total
        st.success(
            f"Precio /m² - Mediana: **{pred_p50:,.0f} €/m²** · Intervalo: **[{pred_p10:,.0f} – {pred_p90:,.0f}] €/m²**\n\n"
            f"Valor total estimado (mediana): **{total_p50:,.0f} €** \n"
            f"Rango total: **[{total_p10:,.0f} – {total_p90:,.0f}] €**"
        )

        # Gráfico de bandas de confianza
        import plotly.graph_objects as go
        fig = go.Figure()
        # Barra mediana
        fig.add_trace(go.Indicator(
            mode="number+gauge+delta",
            value=pred_p50,
            number={'suffix':" €/m²"},
            delta={'reference': pred_p10, 'increasing': {'color': '#3FA34D'}, 'decreasing': {'color': '#AA1927'}},
            gauge={'shape': "bullet",
                   'axis': {'range': [max(0,pred_p10*0.8), pred_p90*1.2]},
                   'bar': {'color':'#1B3B6F'},
                   'threshold': {'line': {'color': "#AA1927", 'width': 3}, 'thickness': 0.75, 'value': pred_p90}},
            domain={'x':[0,1],'y':[0,1]}
        ))
        fig.update_layout(height=160, margin=dict(l=10,r=10,t=10,b=10))
        st.plotly_chart(fig, use_container_width=True)

        # Importancia de variables (si disponible)
        st.markdown("---")
        st.subheader("¿Qué variables pesan más en esta predicción?")
        if shap_explainer is not None:
            try:
                import shap
                # shap_explainer puede recibir el DataFrame directamente
                shap_values = shap_explainer(X_input)
                # shap_values.values es un array (n_rows x n_features)
                shap_vals = shap_values.values[0]
                # Selecciona top 10 características por valor absoluto
                abs_vals = np.abs(shap_vals)
                top_idx = np.argsort(abs_vals)[-10:][::-1]
                top_features = [feature_cols[i] for i in top_idx]
                top_shap = shap_vals[top_idx]
                fig_imp = px.bar(x=np.abs(top_shap)[::-1], y=[top_features[j] for j in range(len(top_features))][::-1], orientation="h",
                                 title="Impacto de características (SHAP)")
                st.plotly_chart(fig_imp, use_container_width=True)
            except Exception as e:
                st.write("No se pudieron calcular los valores SHAP: ", e)
        else:
            st.write("Las importancias de variables no están disponibles en este momento.")

# ==============================
# Botón de regreso al Asistente
# ==============================
if st.button("⬅️ Volver al Asistente", use_container_width=True):
    st.switch_page("pages/1_Asistente.py")
