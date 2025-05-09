import streamlit as st
from Deficit import app as deficit_app
from Disponibilidad import app as disponibilidad_app

st.set_page_config(layout="wide")

st.title("SENtinel")
st.markdown("---")

seleccion = st.selectbox(
    "Seleccione qué analizar",
    ["Deficit", "Disponibilidad"]
)

if seleccion == "Deficit":
    deficit_app()
else:
    disponibilidad_app()
