import streamlit as st
import os, base64

# ==============================
# CSS personalizado
# ==============================
def inject_css():
    """Inyecta la hoja de estilos personalizada en la app."""
    try:
        with open("assets/style.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("⚠️ No se encontró assets/style.css. Verifica la ruta.")


# ==============================
# Función auxiliar para cargar imágenes en base64
# ==============================
def _load_base64_image(path):
    """Carga imagen desde assets y la devuelve codificada en base64."""
    if os.path.exists(path):
        try:
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode()
        except Exception:
            return ""
    return ""


# ==============================
# Cabecera lateral con logos
# ==============================
def sidebar_header():
    """
    Inserta en la parte superior del menú lateral
    los logos institucionales (UCM y SmartHousing).
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    logo_app_path = os.path.join(base_dir, "..", "assets", "logontic.svg")
    logo_ucm_path = os.path.join(base_dir, "..", "assets", "logoucm.png")

    encoded_logo_app = _load_base64_image(logo_app_path)
    encoded_logo_ucm = _load_base64_image(logo_ucm_path)

    css = """
    <style>
    .sidebar-logos {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        padding: 10px 5px 17px 5px;
    }
    .sidebar-logos img {
        max-height: 30px;
    }
    </style>
    """

    logos_html = "<div class='sidebar-logos'>"
    if encoded_logo_ucm:
        logos_html += f"<img src='data:image/png;base64,{encoded_logo_ucm}' alt='UCM'/>"
    if encoded_logo_app:
        logos_html += f"<img src='data:image/svg+xml;base64,{encoded_logo_app}' alt='SmartHousing'/>"
    logos_html += "</div>"

    st.sidebar.markdown(css + logos_html, unsafe_allow_html=True)


# ==============================
# Hero principal con skyline y título dinámico
# ==============================
def hero():
    """
    Renderiza el hero con fondo skyline animado, overlay y textos dinámicos.
    - Usa logo.png en la pantalla principal (landing).
    - Usa isotipo.png en pantallas secundarias (comprar, vender, etc.).
    """
    objetivo = st.session_state.get("objetivo", None)

    if objetivo == "comprar":
        title, subtitle = "Comprar vivienda", "Encuentra tu hogar ideal con datos precisos."
    elif objetivo == "vender":
        title, subtitle = "Vender propiedad", "Valora tu vivienda y elige el mejor momento."
    elif objetivo == "explorar":
        title, subtitle = "Explorar barrios", "Descubre zonas y compara sus características."
    elif objetivo == "avanzadas":
        title, subtitle = "Vistas avanzadas", "Analiza en profundidad con datos completos."
    else:
        title, subtitle = "", "Encuentra el mejor lugar, en el mejor momento."

    base_dir = os.path.dirname(os.path.abspath(__file__))
    skyline_path = os.path.join(base_dir, "..", "assets", "madrid_skyline.png")
    encoded_bg = _load_base64_image(skyline_path)

    logo_path = os.path.join(base_dir, "..", "assets", "logo.png")
    isotipo_path = os.path.join(base_dir, "..", "assets", "isotipo.png")
    encoded_logo = _load_base64_image(logo_path)
    encoded_isotipo = _load_base64_image(isotipo_path)

    if objetivo is None:
        img_html = f"<img src='data:image/png;base64,{encoded_logo}' alt='Logo' style='max-height:420px;margin-bottom:1rem;'/>" if encoded_logo else ""
    else:
        img_html = f"<img src='data:image/png;base64,{encoded_isotipo}' alt='Isotipo' style='max-height:300px;margin-bottom:0.5rem;'/>" if encoded_isotipo else ""

    css = f"""
    <style>
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(-20px); }}
        to   {{ opacity: 1; transform: translateY(0); }}
    }}
    @keyframes moveSkyline {{
        from {{ background-position: 0 bottom; }}
        to   {{ background-position: -1000px bottom; }}
    }}
    .hero {{
        position: relative;
        border-radius: 18px;
        overflow: hidden;
        padding: 60px 40px;
        color: white;
        text-align: center;
        box-shadow: 0 12px 28px rgba(0,0,0,.15);
        animation: fadeIn 1.2s ease both, moveSkyline 120s linear infinite;
        background: url('data:image/png;base64,{encoded_bg}') repeat-x bottom;
        background-size: contain;
    }}
    .hero-overlay {{
        position: absolute;
        inset: 0;
        border-radius: 18px;
        background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6));
        z-index: 0;
    }}
    .hero-content {{
        position: relative;
        z-index: 1;
    }}
    .hero-content h1 {{
        font-size: 2.6rem;
        font-weight: 900;
        margin-bottom: 0.5rem;
    }}
    .hero-content p {{
        font-size: 1.2rem;
        opacity: 0.95;
    }}
    </style>
    """

    html = f"""
    {css}
    <div class="hero">
        <div class="hero-overlay"></div>
        <div class="hero-content">
            {img_html}
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


# ==============================
# KPIs simples
# ==============================
def kpi(title, value, delta=None):
    """
    Muestra un indicador clave (KPI) con título, valor y variación.
    Ejemplo: Precio medio, variación % respecto al año anterior, etc.
    """
    delta_html = ""
    if isinstance(delta, (int, float)):
        color = "#3FA34D" if delta >= 0 else "#AA1927"
        arrow = "↑" if delta >= 0 else "↓"
        delta_html = f"<div style='color:{color};font-weight:700'>{arrow} {abs(delta)}%</div>"

    st.markdown(
        f"""
        <div class='kpi'>
            <div style='font-size:.9rem;color:#555'>{title}</div>
            <div style='font-size:1.6rem;font-weight:800'>{value}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==============================
# Chips para etiquetas rápidas
# ==============================
def chip(text):
    """Muestra una etiqueta de texto tipo 'chip'."""
    st.markdown(f"<span class='chip'>{text}</span>", unsafe_allow_html=True)


# ==============================
# NUEVO: Tarjetas tipo botón (como en tu captura)
# ==============================
def card_buttons(precio_ciudad, distrito_caro, distrito_barato, variacion):
    """
    Renderiza cuatro tarjetas tipo botón (informativas y responsive).
    Los valores se reciben como parámetros para que sean dinámicos.
    """

    css = """
    <style>
    .card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0px 2px 6px rgba(0,0,0,0.1);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .card:hover {
        transform: translateY(-4px);
        box-shadow: 0px 4px 12px rgba(0,0,0,0.2);
    }
    .card p {
        font-size: 13px;
        color: gray;
        margin: 0;
    }
    .card h2, .card h3 {
        margin: 5px 0;
        color: #2e2e2e;
    }
    /* Responsive: pantallas pequeñas */
    @media (max-width: 768px) {
        .card {
            padding: 12px;
        }
        .card h2, .card h3 {
            font-size: 1.2rem;
        }
        .card p {
            font-size: 12px;
        }
    }
    </style>
    """

    st.markdown(css, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
            <div class="card">
                <p>€/m² (ciudad)</p>
                <h2>{precio_ciudad}</h2>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div class="card">
                <p>Distrito más caro</p>
                <h3>{distrito_caro}</h3>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            f"""
            <div class="card">
                <p>Distrito más barato</p>
                <h3>{distrito_barato}</h3>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col4:
        st.markdown(
            f"""
            <div class="card">
                <p>Variación anual</p>
                <h3>{variacion}</h3>
            </div>
            """,
            unsafe_allow_html=True
        )
