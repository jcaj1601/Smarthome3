import streamlit as st

st.set_page_config(page_title="Power BI", layout="wide", page_icon="📊")
st.title("📊 Dashboard Power BI")

st.markdown(
    """
    <iframe title="TFM4"
            width="1140"
            height="541.25"
            src="https://app.powerbi.com/reportEmbed?reportId=e2257188-1697-4136-8a63-bc2a66629215&autoAuth=true&ctid=2b079dc7-e2ea-45bc-9182-0fde14b549b1"
            frameborder="0"
            allowFullScreen="true"></iframe>
    """,
    unsafe_allow_html=True
)
