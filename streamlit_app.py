import streamlit as st
import sys
import os

# Agregar el directorio raíz al path para importar las aplicaciones
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Importar las aplicaciones específicas
from Visualizacion.app import main as run_main_app

# Ejecutar la aplicación principal
run_main_app()
