import os
import subprocess

import streamlit as st

"""
Panel de administración
======================

Esta página permite a los usuarios con privilegios de administración cargar nuevos
datasets y artefactos de modelos sin necesidad de modificar el código fuente.
También ofrece un acceso directo para reentrenar los modelos cuantilícos con el
dataset actual utilizando el script `train_quantiles.py` proporcionado en el
repositorio.

Para proteger el acceso se implementa una verificación de contraseña sencilla.
Es recomendable definir la contraseña de administrador mediante `st.secrets` en
el archivo `.streamlit/secrets.toml`, por ejemplo:

```toml
[general]
admin_password = "cambiar_esta_contraseña"
```

Si no se define `admin_password` en secrets, se usará la contraseña
predeterminada "admin". Cambie esta contraseña antes de desplegar a
producción.
"""

st.set_page_config(page_title="Panel de administración", layout="wide", page_icon="🔧")

# Leer contraseña desde secrets o usar valor por defecto
ADMIN_PASSWORD = st.secrets.get("admin_password", "admin")

if "is_admin" not in st.session_state:
    st.session_state["is_admin"] = False

def login_form():
    """Renderiza el formulario de acceso y actualiza el estado de sesión."""
    st.header("Acceso de administrador")
    password = st.text_input("Contraseña", type="password")
    if st.button("Acceder", use_container_width=True):
        if password == ADMIN_PASSWORD:
            st.session_state["is_admin"] = True
            st.success("Acceso concedido. Puedes actualizar datasets y modelos.")
        else:
            st.error("Contraseña incorrecta. Inténtalo de nuevo.")

# Mostrar login si el usuario no está autenticado
if not st.session_state["is_admin"]:
    login_form()
    st.stop()

# Sección para gestionar datasets
st.header("Gestión de datos")
st.write("Sube un nuevo dataset para sustituir el existente. El archivo se guardará en la carpeta `data/`. Puedes utilizar archivos CSV o Excel.")
dataset_file = st.file_uploader("Archivo de dataset (CSV o Excel)", type=["csv", "xlsx", "xls"])

if dataset_file is not None:
    save_name = "vivienda_imputada" + os.path.splitext(dataset_file.name)[1]
    target_path = os.path.join("data", save_name)
    if st.button("Guardar dataset", use_container_width=True):
        # Crear directorio si no existe
        os.makedirs("data", exist_ok=True)
        with open(target_path, "wb") as f:
            f.write(dataset_file.getbuffer())
        st.success(f"Dataset guardado como `{target_path}`. Ahora puedes reentrenar los modelos si lo deseas.")

st.markdown("---")

# Sección para subir modelos
st.header("Gestión de modelos")
st.write("Carga tus modelos cuantilícos y artefactos asociados. Los archivos se almacenarán en la carpeta `models/` con nombres estándar.")

model_p10_file = st.file_uploader("Modelo P10 (.pkl)", type=["pkl"], key="model_p10")
model_p50_file = st.file_uploader("Modelo P50 (.pkl)", type=["pkl"], key="model_p50")
model_p90_file = st.file_uploader("Modelo P90 (.pkl)", type=["pkl"], key="model_p90")
preprocessor_file = st.file_uploader("Preprocesador (.pkl) opcional", type=["pkl"], key="preproc")
shap_file = st.file_uploader("Explainer SHAP (.pkl) opcional", type=["pkl"], key="shap")

if st.button("Guardar modelos", use_container_width=True):
    os.makedirs("models", exist_ok=True)
    uploads = [
        (model_p10_file, "model_p10.pkl"),
        (model_p50_file, "model_p50.pkl"),
        (model_p90_file, "model_p90.pkl"),
        (preprocessor_file, "preprocessor.pkl"),
        (shap_file, "shap_explainer.pkl"),
    ]
    saved_any = False
    for file, name in uploads:
        if file is not None:
            with open(os.path.join("models", name), "wb") as f:
                f.write(file.getbuffer())
            saved_any = True
    if saved_any:
        st.success("Los modelos y artefactos han sido actualizados correctamente.")
    else:
        st.info("No se subió ningún archivo. Selecciona al menos un modelo para guardar.")

st.markdown("---")

# Sección para reentrenar modelos desde la interfaz
st.header("Entrenamiento de modelos cuantilícos")
st.write("Puedes ejecutar el script `train_quantiles.py` con el dataset actual para crear nuevos modelos P10–P90. Este proceso puede tardar varios minutos y requiere que las dependencias estén instaladas.")

if st.button("Entrenar modelos con dataset actual", use_container_width=True):
    with st.spinner("Entrenando modelos... esto puede tardar varios minutos."):
        try:
            # Ejecutar el script en un subproceso; captura la salida para depuración
            result = subprocess.run(["python", "train_quantiles.py"], capture_output=True, text=True)
            if result.returncode == 0:
                st.success("Entrenamiento completado. Los nuevos modelos están en la carpeta 'models/'.")
            else:
                st.error("Se produjo un error al entrenar los modelos. Consulta el registro para más detalles.")
                st.code(result.stderr)
        except Exception as e:
            st.error(f"No se pudo ejecutar el script de entrenamiento: {e}")

st.markdown("---")

st.header("Cerrar sesión")
if st.button("Cerrar sesión", use_container_width=True):
    st.session_state["is_admin"] = False
    st.success("Sesión cerrada. Recarga la página para volver al inicio.")