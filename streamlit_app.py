import streamlit as st
import sys
import os

# Configuración de rutas para importaciones
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Importar el módulo app directamente
from Visualizacion.app import main as run_main_app

# Ejecutar la aplicación principal
run_main_app()
