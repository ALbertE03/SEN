import streamlit as st
from Visualizacion.Inicio import app as inicio_app
from Visualizacion.Deficit import app as deficit_app
from Visualizacion.Disponibilidad import app as disponibilidad_app
from Visualizacion.comparativas import app as comparativas_app

# Configuración de la página
st.set_page_config(
    page_title="SENtinel",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

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

# Ejecutar la aplicación
if __name__ == "__main__":
    main()
