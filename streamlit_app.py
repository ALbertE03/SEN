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

# Verificar estructura de directorios
current_dir = os.path.dirname(os.path.abspath(__file__))
st.sidebar.title("SENtinel")
st.sidebar.markdown("---")

# Listar el directorio Visualizacion para diagnóstico
vis_dir = os.path.join(current_dir, "Visualizacion")
if os.path.exists(vis_dir):
    files = os.listdir(vis_dir)
    
    # Verificar nombres de archivos
    inicio_file = None
    for file in files:
        if file.lower() == "inicio.py":
            inicio_file = file
            break
    
    # Definir las opciones del menú
    menu = st.sidebar.radio("Menu:", ["Inicio", "Déficit", "Disponibilidad", "Comparativas"])
    
    try:
        # Configurar paths
        if vis_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        # Importar módulos de forma dinámica según los archivos disponibles
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
        st.write("Archivos disponibles en Visualizacion:")
        st.write(files)
        
        # Mostrar información de diagnóstico
        st.write("Detalles del sistema:")
        st.write(f"Directorio actual: {current_dir}")
        st.write(f"Python path: {sys.path}")
        
        # Intentar importar un módulo simple para prueba
        try:
            import pandas as pd
            st.success("pandas se importó correctamente")
        except:
            st.error("Problema importando pandas")
else:
    st.error(f"El directorio {vis_dir} no existe. Verifique la estructura del repositorio.")
    st.write(f"Contenido del directorio {current_dir}:")
    st.write(os.listdir(current_dir))
