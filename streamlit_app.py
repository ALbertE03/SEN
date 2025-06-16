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

# Obtener la ruta absoluta del directorio actual
current_dir = os.path.dirname(os.path.abspath(__file__))

# Agregar la ruta al path para importaciones
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Importamos directamente los módulos necesarios
try:
    from Visualizacion.Inicio import app as inicio_app
    from Visualizacion.Deficit import app as deficit_app
    from Visualizacion.Disponibilidad import app as disponibilidad_app
    from Visualizacion.comparativas import app as comparativas_app
    
    # Función principal
    def main():
        # Barra lateral con menú de navegación
        st.sidebar.title("SENtinel")
        st.sidebar.markdown("---")
        # Opciones de navegación
        menu = st.sidebar.radio("Menu:", ["Inicio", "Déficit", "Disponibilidad", "Comparativas"])
        
        # Mostrar la página seleccionada
        if menu == "Inicio":
            inicio_app()
        elif menu == "Déficit":
            deficit_app()
        elif menu == "Disponibilidad":
            disponibilidad_app()
        elif menu == "Comparativas":
            comparativas_app()
    
    # Ejecutar la función principal
    main()
    
except ImportError as e:
    st.error(f"Error al importar módulos: {e}")
    st.write("Detalles del sistema:")
    st.write(f"Directorio actual: {current_dir}")
    st.write(f"Python path: {sys.path}")
      # Intentar listar los archivos en el directorio de visualización
    vis_dir = os.path.join(current_dir, "Visualizacion")
    try:
        if os.path.exists(vis_dir):
            st.write(f"Contenido de {vis_dir}:")
            st.write(os.listdir(vis_dir))
        else:
            st.error(f"El directorio {vis_dir} no existe")
    except Exception as e:
        st.error(f"Error al listar directorio: {e}")
