import streamlit as st
from Deficit import app as deficit_app
from Disponibilidad import app as disponibilidad_app

st.set_page_config(layout="wide")

st.title("SENtinel")
st.warning("el 3-4 de septiembre no están en cubadebate, no son -SEN")
st.warning("19-22 de octubre -SEN")
st.warning("7-11 noviembre -SEN")
st.warning("4 dic - SEN")
st.warning("2025- 17 enero,2 febrero,19 y 28 marzo, 19 abril no estan en cubadebate")
st.warning("16-16 marzo -SEN")
st.markdown("---")

seleccion = st.selectbox("Seleccione qué analizar", ["Deficit", "Disponibilidad"])

if seleccion == "Deficit":
    deficit_app()
else:
    disponibilidad_app()
