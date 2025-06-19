import streamlit as st
import sys
import os
import importlib

# Configuración de la página
st.set_page_config(
    page_title="SENtinel",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Directorio principal
current_dir = os.path.dirname(os.path.abspath(__file__))
st.sidebar.title("SENtinel")
st.sidebar.markdown("---")

# Verificar directorio de visualizaciones
vis_dir = os.path.join(current_dir, "Visualizacion")
if os.path.exists(vis_dir):
    files = os.listdir(vis_dir)
    
    # Buscar archivo de inicio (puede ser Inicio.py o inicio.py)
    inicio_file = None
    for file in files:
        if file.lower() == "inicio.py":
            inicio_file = file
            break
    
    # Menú principal
    menu = st.sidebar.radio("Menu:", ["Inicio", "Déficit", "Disponibilidad", "Comparativas"])
    
    try:
        # Importar dependencias necesarias
        import pandas as pd
        import plotly.express as px
        import plotly.graph_objects as go
        
        # Configurar paths
        if vis_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        # Cargar el módulo correspondiente según la selección del menú
        if menu == "Inicio" and inicio_file:
            module_name = f"Visualizacion.{inicio_file[:-3]}"  # Quitar .py
            inicio_module = importlib.import_module(module_name)
            inicio_module.app()
        elif menu == "Déficit":
            deficit_module = importlib.import_module("Visualizacion.Deficit")
            deficit_module.app()
        elif menu == "Disponibilidad":
            disponibilidad_module = importlib.import_module("Visualizacion.Disponibilidad")
            disponibilidad_module.app()
        elif menu == "Comparativas":
            comparativas_module = importlib.import_module("Visualizacion.comparativas")
            comparativas_module.app()
        else:
            st.error(f"No se encontró el módulo para {menu}")
            st.write(f"Archivos disponibles: {files}")
    except Exception as e:
        st.error(f"Error al cargar módulos: {str(e)}")
        st.info("Compruebe que todas las dependencias están instaladas y que la estructura del proyecto es correcta.")
else:
    st.error(f"El directorio {vis_dir} no existe. Verifique la estructura del repositorio.")
    st.write(f"Contenido del directorio {current_dir}:")
    st.write(os.listdir(current_dir))
