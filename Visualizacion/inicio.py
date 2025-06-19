import streamlit as st
import pandas as pd
from datetime import datetime
from .utils import cargar_datos, preparar_dataframe_basico

def app():
    st.header("Reporte Diario")
    st.markdown("---")
    
    entradas = cargar_datos()
    df = preparar_dataframe_basico(entradas)
    
    # Obtener el último día disponible y ordenar por fecha
    entradas_ordenadas = sorted(entradas, key=lambda x: x["fecha"], reverse=True)
    
    # Último día disponible
    ultimo_dia = entradas_ordenadas[0]
    fecha_ultimo = ultimo_dia["fecha"]
    
    # Crear un diccionario de fechas disponibles para búsqueda rápida
    fechas_disponibles = {e["fecha"].date(): e for e in entradas}
    
    # Obtener todas las fechas disponibles para el selector
    todas_fechas = sorted(list(fechas_disponibles.keys()), reverse=True)
    fecha_minima = todas_fechas[-1] if todas_fechas else fecha_ultimo.date()
    fecha_maxima = fecha_ultimo.date()
    
    # Selector de fecha en la barra lateral
    with st.sidebar:
        st.subheader("Selección de fecha")
        fecha_seleccionada = st.date_input(
            "Seleccione una fecha para visualizar datos:",
            value=fecha_ultimo.date(),
            min_value=fecha_minima,
            max_value=fecha_maxima,
            key="fecha_selector_inicio"
        )
        
        # Mostrar información sobre disponibilidad de datos
        if fecha_seleccionada not in fechas_disponibles:
            st.warning("⚠️ No hay datos disponibles para esta fecha. Se mostrarán los datos del último día disponible.")
            fecha_seleccionada = fecha_ultimo.date()
        elif fecha_seleccionada == fecha_ultimo.date():
            st.success("✓ Mostrando los datos más recientes disponibles.")
        else:
            st.info(f"ℹ️ Mostrando datos históricos del {fecha_seleccionada.strftime('%d/%m/%Y')}. La fecha más reciente disponible es {fecha_ultimo.date().strftime('%d/%m/%Y')}.")
    
    # Obtener el día seleccionado y su día anterior para comparación
    dia_seleccionado = fechas_disponibles.get(fecha_seleccionada, ultimo_dia)
    fecha_seleccionada_dt = dia_seleccionado["fecha"]
    
    # Buscar el día anterior al seleccionado para comparaciones
    dia_anterior = None
    fecha_anterior_idx = todas_fechas.index(fecha_seleccionada) + 1 if fecha_seleccionada in todas_fechas else None
    if fecha_anterior_idx is not None and fecha_anterior_idx < len(todas_fechas):
        fecha_anterior = todas_fechas[fecha_anterior_idx]
        dia_anterior = fechas_disponibles.get(fecha_anterior)
    
    # Panel superior con información clave
    st.subheader(f"Datos del {fecha_seleccionada_dt.strftime('%d/%m/%Y')}")
      # Mostrar los datos en forma de tabla con métricas destacadas
    datos = dia_seleccionado["datos"]
    pred = datos.get("prediccion", {})
    
    # Datos del día anterior para comparación
    datos_anteriores = {}
    if dia_anterior:
        datos_anteriores = dia_anterior["datos"].get("prediccion", {})
    
    # Crear métricas destacadas en una fila
    col1, col2, col3, col4 = st.columns(4)
    
    # Función para calcular delta con indicador de dirección y con color personalizado
    def calcular_delta_personalizado(actual, anterior, es_bueno_si_aumenta=True):
        if actual is None or anterior is None or actual == "N/D" or anterior == "N/D":
            return None
            
        valor_actual = float(actual)
        valor_anterior = float(anterior)
        diferencia = valor_actual - valor_anterior
        
        # Si no hay cambio, retornar 0
        if diferencia == 0:
            return 0
        
        # La dirección de la flecha siempre muestra la dirección real del cambio
        # El color indica si el cambio es bueno (verde) o malo (rojo)
        # Si es bueno si aumenta y aumentó, o es bueno si disminuye y disminuyó -> verde
        # En caso contrario -> rojo
        if (diferencia > 0 and es_bueno_si_aumenta) or (diferencia < 0 and not es_bueno_si_aumenta):
            # Mantenemos diferencia positiva para verde y negativa para rojo
            return diferencia
        else:
            # Streamlit usa color verde para valores positivos y rojo para negativos
            # Usamos delta_color="inverse" para invertir esta lógica
            # La flecha seguirá la dirección real pero el color será invertido
            return diferencia
    
    with col1:
        # Para Déficit: si aumenta -> flecha arriba roja, si disminuye -> flecha abajo verde
        deficit_actual = pred.get("deficit", "N/D")
        deficit_anterior = datos_anteriores.get("deficit", "N/D")
        
        delta_deficit = None
        if deficit_actual != "N/D" and deficit_anterior != "N/D":
            # Para déficit, un aumento es malo (rojo)
            delta_deficit = calcular_delta_personalizado(deficit_actual, deficit_anterior, es_bueno_si_aumenta=False)
        
        # El parámetro delta_color="inverse" invierte los colores: valor positivo->rojo, valor negativo->verde
        st.metric(
            label="Déficit (MW)",
            value=deficit_actual,
            delta=delta_deficit,
            delta_color="inverse" if delta_deficit and delta_deficit > 0 else "normal"
        )
    
    with col2:
        # Para Disponibilidad: si aumenta -> flecha arriba verde, si disminuye -> flecha abajo roja
        disp_actual = pred.get("disponibilidad", "N/D")
        disp_anterior = datos_anteriores.get("disponibilidad", "N/D")
        
        delta_disp = None
        if disp_actual != "N/D" and disp_anterior != "N/D":
            # Para disponibilidad, un aumento es positivo (verde)
            delta_disp = calcular_delta_personalizado(disp_actual, disp_anterior, es_bueno_si_aumenta=True)
        
        st.metric(
            label="Disponibilidad (MW)",
            value=disp_actual,
            delta=delta_disp
        )
    
    with col3:
        # Para Demanda Máxima: si aumenta -> flecha arriba roja, si disminuye -> flecha abajo verde
        demanda_actual = pred.get("demanda_maxima", "N/D")
        demanda_anterior = datos_anteriores.get("demanda_maxima", "N/D")
        
        delta_demanda = None
        if demanda_actual != "N/D" and demanda_anterior != "N/D":
            # Para demanda máxima, un aumento es negativo (rojo)
            delta_demanda = calcular_delta_personalizado(demanda_actual, demanda_anterior, es_bueno_si_aumenta=False)
        
        st.metric(
            label="Demanda Máxima (MW)",
            value=demanda_actual,
            delta=delta_demanda,
            delta_color="inverse" if delta_demanda and delta_demanda > 0 else "normal"
        )
    
    with col4:
        # Para Afectación: si aumenta -> flecha arriba roja, si disminuye -> flecha abajo verde
        afect_actual = pred.get("afectacion", "N/D")
        afect_anterior = datos_anteriores.get("afectacion", "N/D")
        
        delta_afect = None
        if afect_actual != "N/D" and afect_anterior != "N/D":
            # Para afectación, un aumento es negativo (rojo)
            delta_afect = calcular_delta_personalizado(afect_actual, afect_anterior, es_bueno_si_aumenta=False)
        
        st.metric(
            label="Afectación (MW)",
            value=afect_actual,
            delta=delta_afect,
            delta_color="inverse" if delta_afect and delta_afect > 0 else "normal"
        )
    
    
    
    # Estado de las plantas
    st.write("### Estado de las Centrales Termoeléctricas")
    
    # Contenedor para las plantas
    plantas_tab1, plantas_tab2, plantas_tab3 = st.tabs(["Plantas en avería", "Plantas en mantenimiento", "Limitaciones"])
    
    with plantas_tab1:
        # Plantas en avería
        plantas_en_averia = datos.get("plantas", {}).get("averia", [])
        if plantas_en_averia:
            # Crear una lista formateada de plantas con sus unidades
            plantas_data = []
            for planta in plantas_en_averia:
                nombre_planta = planta.get("planta", "No disponible")
                unidades = planta.get("unidades", [])
                
                # Formatear las unidades para presentación
                if unidades:
                    # Filtrar valores nulos y formatear
                    unidades_filtradas = [u for u in unidades if u is not None]
                    if unidades_filtradas:
                        unidades_str = ", ".join([str(u) for u in unidades_filtradas])
                        plantas_data.append({
                            "Central Termoeléctrica": nombre_planta,
                            "Unidades fuera de servicio": unidades_str
                        })
                    else:
                        plantas_data.append({
                            "Central Termoeléctrica": nombre_planta,
                            "Unidades fuera de servicio": "Todas/No especificado"
                        })
                else:
                    plantas_data.append({
                        "Central Termoeléctrica": nombre_planta,
                        "Unidades fuera de servicio": "No especificado"
                    })
            
            # Mostrar tabla de plantas en avería con mejor estilo
            if plantas_data:
                st.dataframe(pd.DataFrame(plantas_data), use_container_width=True)
            else:
                st.info("No hay detalles específicos de las unidades afectadas")
        else:
            st.success("No hay plantas reportadas en avería")
    
    with plantas_tab2:
        # Plantas en mantenimiento
        plantas_en_mantenimiento = datos.get("plantas", {}).get("mantenimiento", [])
        if plantas_en_mantenimiento:
            # Crear una lista formateada de plantas con sus unidades
            mantenimiento_data = []
            for planta in plantas_en_mantenimiento:
                nombre_planta = planta.get("planta", "No disponible")
                unidad = planta.get("unidad")
                unidades = planta.get("unidades", [])
                
                # Formatear las unidades para presentación
                unidades_str = ""
                if unidad:
                    unidades_str = str(unidad)
                elif unidades:
                    # Filtrar valores nulos y formatear
                    unidades_filtradas = [u for u in unidades if u is not None]
                    if unidades_filtradas:
                        unidades_str = ", ".join([str(u) for u in unidades_filtradas])
                
                mantenimiento_data.append({
                    "Central Termoeléctrica": nombre_planta,
                    "Unidades en mantenimiento": unidades_str if unidades_str else "No especificado"
                })
            
            # Mostrar tabla de plantas en mantenimiento con mejor estilo
            st.dataframe(pd.DataFrame(mantenimiento_data), use_container_width=True)
        else:
            st.success("No hay plantas reportadas en mantenimiento programado")
    
    with plantas_tab3:
        # Limitación térmica
        limitacion_termica = datos.get("plantas", {}).get("limitacion_termica", {})
        if limitacion_termica and limitacion_termica.get("mw_afectados"):
            mw_afectados = limitacion_termica.get("mw_afectados", "No disponible")
            tipo = limitacion_termica.get("tipo", "No especificado")
            
            # Mostrar con mejor diseño
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(
                    label="MW Afectados por limitación térmica",
                    value=mw_afectados
                )
            
            with col2:
                st.metric(
                    label="Tipo de limitación",
                    value=tipo if tipo else "No especificado"
                )
        else:
            st.success("No hay limitaciones térmicas reportadas")

    # Dividir en columnas para la información adicional
    st.write("### Otras fuentes de generación")
    
    otras_tab1, otras_tab2, otras_tab3 = st.tabs(["Generación Distribuida", "Energía Renovable", "Zonas Afectadas"])
    
    with otras_tab1:
        distribuida = datos.get("distribuida", {})
        
        # Motores con problemas
        motores_problemas = distribuida.get("motores_con_problemas", {})
        if motores_problemas and motores_problemas.get("impacto_mw"):
            st.subheader("Motores fuera de servicio")
            
            # Crear columnas para visualización
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    label="Total de motores afectados",
                    value=motores_problemas.get("total", "No especificado")
                )
            
            with col2:
                st.metric(
                    label="Impacto en MW",
                    value=motores_problemas.get("impacto_mw", "No disponible")
                )
            
            with col3:
                st.metric(
                    label="Causa principal",
                    value=motores_problemas.get("causa", "No especificada").capitalize()
                )
        
        # Patanas con problemas
        patanas_con_problemas = distribuida.get("patanas_con_problemas", [])
        if patanas_con_problemas:
            st.subheader("Patanas con problemas")
            
            patanas_data = []
            for patana in patanas_con_problemas:
                patanas_data.append({
                    "Nombre": patana.get("nombre", "No especificado"),
                    "Ubicación": patana.get("ubicacion", "No especificada"),
                    "MW afectados": patana.get("mw_afectados", "No especificado")
                })
            
            st.dataframe(pd.DataFrame(patanas_data), use_container_width=True)
        
        # Problemas de lubricantes
        problemas_lubricantes = distribuida.get("problemas_lubricantes", {})
        if problemas_lubricantes and (problemas_lubricantes.get("mw_afectados") or problemas_lubricantes.get("unidades_afectadas")):
            st.subheader("Problemas de lubricantes")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(
                    label="MW afectados",
                    value=problemas_lubricantes.get("mw_afectados", "No especificado")
                )
            
            with col2:
                st.metric(
                    label="Unidades afectadas",
                    value=problemas_lubricantes.get("unidades_afectadas", "No especificado")
                )
        
        if not motores_problemas.get("impacto_mw") and not patanas_con_problemas and not problemas_lubricantes.get("mw_afectados"):
            st.info("No hay datos reportados sobre problemas en la generación distribuida")
    
    with otras_tab2:
        # Paneles solares
        paneles_solares = datos.get("paneles_solares", {})
        
        if paneles_solares and (paneles_solares.get("produccion_mwh") or paneles_solares.get("cantidad_parques")):
            st.subheader("Parques solares fotovoltaicos")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(
                    label="Cantidad de parques",
                    value=paneles_solares.get("cantidad_parques", "No especificado")
                )
                
                st.metric(
                    label="Capacidad instalada",
                    value=f"{paneles_solares.get('capacidad_instalada', 'No especificado')} MW" 
                    if paneles_solares.get('capacidad_instalada') else "No especificado"
                )
            
            with col2:
                st.metric(
                    label="Producción",
                    value=f"{paneles_solares.get('produccion_mwh', 'No especificado')} MWh" 
                    if paneles_solares.get('produccion_mwh') else "No especificado"
                )
                
                st.metric(
                    label="Nuevos parques",
                    value=paneles_solares.get('nuevos_parques', 'No especificado')
                )
            
            if paneles_solares.get("periodo_produccion"):
                st.info(f"Periodo de producción: {paneles_solares.get('periodo_produccion')}")
        else:
            st.info("No hay datos reportados sobre producción de energía solar fotovoltaica")
    
    with otras_tab3:
        # Zonas con problemas
        zonas_con_problemas = datos.get("zonas_con_problemas", [])
        if zonas_con_problemas:
            st.subheader("Zonas con afectaciones reportadas")
            
            # Crear una lista de zonas afectadas
            zonas_data = []
            for zona in zonas_con_problemas:
                if isinstance(zona, dict):
                    nombre_zona = zona.get("nombre", "No especificado")
                    afectacion = zona.get("afectacion", "No especificada")
                    zonas_data.append({
                        "Zona": nombre_zona,
                        "Afectación": afectacion
                    })
                elif isinstance(zona, str):
                    zonas_data.append({
                        "Zona": zona,
                        "Afectación": "No especificada"
                    })
            
            # Mostrar la tabla de zonas afectadas
            if zonas_data:
                st.dataframe(pd.DataFrame(zonas_data), use_container_width=True)
            else:
                st.info("No hay detalles específicos sobre las zonas afectadas")
        else:
            st.info("No hay zonas con problemas reportadas específicamente")
      # Enlaces relacionados
    with st.expander("Ver enlace original"):
        if "enlace" in ultimo_dia and ultimo_dia["enlace"]:
            st.write(f"Fuente de datos: [Cubadebate]({ultimo_dia['enlace']})")
        else:
            st.write("Enlace a la fuente original no disponible")
