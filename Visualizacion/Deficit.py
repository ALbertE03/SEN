import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import matplotlib.pyplot as plt  # Añadido para soporte de background_gradient
from .utils import (
    cargar_datos,
    preparar_dataframe_basico,
    obtener_plantas,
    datos_estado_plantas
)
from . import mapping

def preparar_dataframe_deficit(entradas):
    """
    Prepara un dataframe específicamente diseñado para análisis de déficit con datos adicionales
    Args:
        entradas (list): Lista de registros de datos eléctricos
    Returns:
        pd.DataFrame: DataFrame con datos procesados para análisis de déficit
    """
    filas = []
    for e in entradas:
        pred = e["datos"].get("prediccion", {})
        info_matutina = e["datos"].get("info_matutina", {})
        impacto = e["datos"].get("impacto", {})
        
        # Calcular el déficit correctamente: si está en predicción usamos ese valor,
        # si no, intentamos calcularlo como (demanda - disponibilidad)
        deficit = pred.get("deficit")
        demanda = pred.get("demanda_maxima")
        disponibilidad = pred.get("disponibilidad")
        
        # Si el déficit no está directamente reportado, calcularlo
        if deficit is None and demanda is not None and disponibilidad is not None:
            if demanda > disponibilidad:
                deficit = demanda - disponibilidad
            else:
                deficit = 0
        
        porcentaje_deficit = ((deficit / demanda) * 100) if deficit is not None and demanda and demanda > 0 else None
        
        # Obtener el máximo impacto reportado
        maximo_impacto = impacto.get("maximo", {}).get("mw") if impacto else None
        
        # Contar plantas en avería usando los nombres estandarizados
        plantas_averia = e["datos"].get("plantas", {}).get("averia", [])
        # Usamos set para evitar plantas duplicadas debido a estandarización
        plantas_estandarizadas = set()
        from .plant_standardizer import get_canonical_plant_name
        
        for p in plantas_averia:
            planta_nombre = p.get("planta")
            if planta_nombre:
                nombre_canonico = get_canonical_plant_name(planta_nombre)
                if nombre_canonico:  # Solo añadir si es un nombre válido
                    plantas_estandarizadas.add(nombre_canonico)
        
        cant_plantas_averia = len(plantas_estandarizadas)
        
        # Motores fuera de servicio
        motores_con_problemas = e["datos"].get("distribuida", {}).get("motores_con_problemas", {})
        impacto_motores_mw = motores_con_problemas.get("impacto_mw")
        
        filas.append({
            "fecha": e["fecha"],
            "afectacion": pred.get("afectacion"),
            "disponibilidad": disponibilidad,
            "demanda": demanda,
            "deficit": deficit,
            "porcentaje_deficit": porcentaje_deficit,
            "respaldo": pred.get("respaldo"),
            "maximo_impacto": maximo_impacto,
            "cant_plantas_averia": cant_plantas_averia,
            "impacto_motores_mw": impacto_motores_mw,
            "deficit_matutino": info_matutina.get("deficit"),
            "dia_semana": e["fecha"].strftime('%A'),
            "mes": e["fecha"].strftime('%B'),
            "año": e["fecha"].year
        })
    
    df = pd.DataFrame(filas).set_index("fecha").sort_index()
    
    # Agregar columnas de tendencia
    df['deficit_7d_avg'] = df['deficit'].rolling(window=7, min_periods=1).mean()
    df['deficit_30d_avg'] = df['deficit'].rolling(window=30, min_periods=1).mean()
    
    return df

def mostrar_indicadores_deficit(df):
    """
    Muestra un conjunto de indicadores KPI relacionados con el déficit
    Args:
        df (pd.DataFrame): DataFrame con datos de déficit procesados
    """
    st.subheader("Indicadores Estadísticos del Período")
    
    # Filtrar valores no nulos para cálculos
    df_deficit_no_nulo = df[df["deficit"].notnull()]
    
    if df_deficit_no_nulo.empty:
        st.error("No hay datos suficientes para calcular indicadores de déficit.")
        return
    
    # Calcular métricas para el período seleccionado
    deficit_promedio = df_deficit_no_nulo["deficit"].mean()
    deficit_mediana = df_deficit_no_nulo["deficit"].median()
    deficit_maximo = df_deficit_no_nulo["deficit"].max()
    deficit_minimo = df_deficit_no_nulo["deficit"].min()
    desviacion_std = df_deficit_no_nulo["deficit"].std()
    
    # Obtener fechas de valores máximos y mínimos
    fecha_max = df_deficit_no_nulo.loc[df_deficit_no_nulo["deficit"] == deficit_maximo].index[0].strftime("%d/%m/%Y") if not df_deficit_no_nulo.empty else "N/D"
    fecha_min = df_deficit_no_nulo.loc[df_deficit_no_nulo["deficit"] == deficit_minimo].index[0].strftime("%d/%m/%Y") if not df_deficit_no_nulo.empty and deficit_minimo > 0 else "N/D"
    
    # Días con déficit
    dias_totales = len(df_deficit_no_nulo)
    dias_con_deficit = len(df_deficit_no_nulo[df_deficit_no_nulo["deficit"] > 0])
    porcentaje_dias_deficit = (dias_con_deficit / dias_totales * 100) if dias_totales > 0 else 0
    
    # Mostrar KPIs en columnas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Déficit Promedio (MW)",
            value=f"{int(deficit_promedio)}" if not pd.isna(deficit_promedio) else "N/D"
        )
        
        st.metric(
            label="Déficit Mediana (MW)",
            value=f"{int(deficit_mediana)}" if not pd.isna(deficit_mediana) else "N/D"
        )
    
    with col2:
        st.metric(
            label=f"Déficit Máximo (MW)",
            value=f"{int(deficit_maximo)}" if not pd.isna(deficit_maximo) else "N/D",
            help=f"Registrado el {fecha_max}"
        )
        
        st.metric(
            label="Déficit Mínimo >0 (MW)",
            value=f"{int(deficit_minimo)}" if not pd.isna(deficit_minimo) and deficit_minimo > 0 else "N/D",
            help=f"Registrado el {fecha_min}"
        )
    
    with col3:
        st.metric(
            label="Desviación Estándar",
            value=f"{int(desviacion_std)}" if not pd.isna(desviacion_std) else "N/D"
        )
        
        st.metric(
            label="Días Analizados",
            value=f"{dias_totales}" if dias_totales > 0 else "N/D"
        )
    
    with col4:
        st.metric(
            label="Días con Déficit",
            value=f"{dias_con_deficit}" if dias_con_deficit >= 0 else "N/D"
        )
        
        st.metric(
            label="% Días con Déficit",
            value=f"{porcentaje_dias_deficit:.1f}%",
            help=f"{dias_con_deficit} días de {dias_totales} analizados"
        )

def analizar_plantas_deficit(entradas, df):
    """
    Realiza un análisis detallado de las plantas y su relación con el déficit energético
    Args:
        entradas (list): Lista de registros de datos eléctricos originales
        df (pd.DataFrame): DataFrame con datos de déficit procesados
    """
    st.subheader("Análisis de Plantas en Avería y su Impacto en el Déficit")
    
    # Extraer datos de plantas en avería por fecha usando plant_standardizer
    datos_plantas = {}  # Estructura: {fecha: [plantas en avería]}
    from .plant_standardizer import get_canonical_plant_name, get_valid_plant_names
    
    for entrada in entradas:
        fecha = entrada["fecha"]
        plantas_averia = entrada["datos"].get("plantas", {}).get("averia", [])
        plantas_estandarizadas = set()
        
        for p in plantas_averia:
            planta_nombre = p.get("planta")
            if planta_nombre:
                nombre_canonico = get_canonical_plant_name(planta_nombre)
                if nombre_canonico:  # Solo añadir si es un nombre válido
                    plantas_estandarizadas.add(nombre_canonico)
        
        if plantas_estandarizadas:  # Solo agregar si hay plantas en avería
            datos_plantas[fecha] = list(plantas_estandarizadas)
    
    if not datos_plantas:
        st.info("No hay datos de plantas en avería disponibles.")
        return
        
    # Crear DataFrame para análisis de frecuencia
    filas_plantas = []
    for fecha, plantas in datos_plantas.items():
        for planta in plantas:
            filas_plantas.append({
                "fecha": fecha,
                "planta": planta
            })
    
    df_plantas = pd.DataFrame(filas_plantas)
    
    # Calcular frecuencia por planta
    if not df_plantas.empty:
        # Contar días en avería por planta
        frecuencia = df_plantas["planta"].value_counts()
        df_freq = pd.DataFrame({
            "planta": frecuencia.index,
            "días_en_avería": frecuencia.values
        }).set_index("planta")
        
        # Selección de planta específica para análisis
        # Solo incluir plantas termoeléctricas válidas
        valid_plants = ["Todas las plantas"] + sorted(set(df_plantas["planta"].unique()) & set(get_valid_plant_names()))
        planta_seleccionada = st.selectbox("Seleccionar planta para análisis", valid_plants)
        
        # Si se seleccionó una planta específica, filtrar los datos
        if planta_seleccionada != "Todas las plantas":
            # Fechas cuando la planta estuvo en avería
            fechas_averia = df_plantas[df_plantas["planta"] == planta_seleccionada]["fecha"].unique()
            
            # Filtrar el dataframe principal para esas fechas
            df_planta_filtrado = df.loc[[fecha for fecha in fechas_averia if fecha in df.index]]
            
            if not df_planta_filtrado.empty:
                # Mostrar indicadores para la planta seleccionada
                deficit_promedio_planta = df_planta_filtrado["deficit"].mean()
                deficit_promedio_general = df["deficit"].mean()
                diferencia = deficit_promedio_planta - deficit_promedio_general
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric(
                        label=f"Días en avería",
                        value=len(fechas_averia)
                    )
                    
                    st.metric(
                        label=f"Déficit promedio cuando {planta_seleccionada} está en avería",
                        value=f"{int(deficit_promedio_planta)} MW" if not pd.isna(deficit_promedio_planta) else "N/D"
                    )
                
                with col2:
                    st.metric(
                        label=f"% del tiempo en avería",
                        value=f"{(len(fechas_averia) / len(df) * 100):.1f}%",
                        help=f"{len(fechas_averia)} días de {len(df)} analizados"
                    )
                    
                    st.metric(
                        label=f"Diferencia vs. déficit promedio general",
                        value=f"{int(diferencia)} MW" if not pd.isna(diferencia) else "N/D",
                        delta=f"{int(diferencia)}" if not pd.isna(diferencia) else None,
                        delta_color="inverse" if diferencia > 0 else "normal"
                    )
                
                # Gráfico de déficit cuando la planta está en avería
                fig = px.scatter(
                    df_planta_filtrado.reset_index(),
                    x="fecha",
                    y="deficit",
                    size="deficit",
                    color="deficit",
                    color_continuous_scale="Reds",
                    title=f"Déficit cuando {planta_seleccionada} está en avería",
                    labels={"fecha": "Fecha", "deficit": "Déficit (MW)"}
                )
                
                # Agregar línea de déficit promedio
                fig.add_hline(
                    y=deficit_promedio_general,
                    line_dash="dash",
                    line_color="blue",
                    annotation_text=f"Déficit promedio general: {int(deficit_promedio_general)} MW"
                )
                
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
        
        # Visualización de frecuencia de averías por planta
        st.write("### Frecuencia de averías por planta")
        
        # Selección del tipo de visualización
        vista_seleccionada = st.radio(
            "Tipo de visualización:",
            ["Tabla de frecuencias", "Gráfico de barras"],
            key="vista_analisis_plantas"
        )
        
        # Mostrar visualización según selección
        if not df_freq.empty:
            # Filtrar para mostrar solo plantas termoeléctricas válidas
            df_freq_filtrado = df_freq[df_freq.index.isin(get_valid_plant_names())]
            
            if vista_seleccionada == "Tabla de frecuencias":
                st.write("Frecuencia de averías por planta:")
                try:
                    st.dataframe(df_freq_filtrado.style.background_gradient(cmap='YlOrRd'))
                except Exception as e:
                    st.error(f"Error al mostrar tabla con formato: {str(e)}")
                    # Mostrar tabla sin formato como fallback
                    st.dataframe(df_freq_filtrado)
            else:
                # Preparar datos para gráfico
                df_graph = df_freq_filtrado.reset_index().sort_values('días_en_avería', ascending=True).tail(10)
                fig = px.bar(
                    df_graph,
                    x='días_en_avería',
                    y='planta',
                    title="Top 10 plantas con más días en avería",
                    labels={'días_en_avería': 'Días en avería', 'planta': 'Planta'},
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)

def analizar_distribucion_temporal_deficit(df):
    """
    Analiza la distribución temporal del déficit por días de semana, meses y estacionalidad
    Args:
        df (pd.DataFrame): DataFrame con datos de déficit procesados
    """
    st.subheader("Distribución Temporal del Déficit")
    
    # Crear 3 columnas para visualizaciones
    col1, col2 = st.columns(2)
    
    with col1:
        # Análisis por día de la semana
        st.write("#### Déficit por día de semana")
        
        # Mapping para traducir los nombres de los días
        dias = {
            'Monday': 'Lunes',
            'Tuesday': 'Martes',
            'Wednesday': 'Miércoles',
            'Thursday': 'Jueves',
            'Friday': 'Viernes',
            'Saturday': 'Sábado',
            'Sunday': 'Domingo'
        }
        
        # Orden correcto de los días
        dias_orden = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        # Calcular déficit promedio por día de semana
        if "dia_semana" not in df.columns:
            df.loc[:, "dia_semana"] = df.index.strftime('%A')
        
        deficit_por_dia = df.groupby('dia_semana')['deficit'].mean()
        
        # Reordenar según el orden de días correcto
        deficit_por_dia = deficit_por_dia.reindex(dias_orden)
        
        # Traducir los nombres
        deficit_por_dia.index = [dias.get(dia, dia) for dia in deficit_por_dia.index]
        
        # Crear gráfico
        fig = px.bar(
            x=deficit_por_dia.index,
            y=deficit_por_dia.values,
            labels={'x': 'Día de la semana', 'y': 'Déficit (MW)'},
            title="Déficit promedio por día de la semana",
            color=deficit_por_dia.values,
            color_continuous_scale='Reds'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Análisis por mes
        st.write("#### Déficit por mes")
        
        # Mapping para traducir los nombres de los meses
        meses = {
            'January': 'Enero',
            'February': 'Febrero',
            'March': 'Marzo',
            'April': 'Abril',
            'May': 'Mayo',
            'June': 'Junio',
            'July': 'Julio',
            'August': 'Agosto',
            'September': 'Septiembre',
            'October': 'Octubre',
            'November': 'Noviembre',
            'December': 'Diciembre'
        }
        
        # Crear columna de mes numérico
        if "mes_num" not in df.columns:
            df.loc[:, "mes_num"] = df.index.month
        
        # Calcular déficit promedio por mes
        deficit_por_mes = df.groupby('mes_num')['deficit'].mean()
        
        # Crear gráfico
        meses_orden = list(range(1, 13))
        nombre_meses = [meses[datetime(2022, m, 1).strftime('%B')] for m in meses_orden]
        
        # Reindexar para mostrar todos los meses
        deficit_por_mes = deficit_por_mes.reindex(meses_orden)
        
        fig = px.bar(
            x=nombre_meses,
            y=deficit_por_mes.values,
            labels={'x': 'Mes', 'y': 'Déficit (MW)'},
            title="Déficit promedio por mes",
            color=deficit_por_mes.values,
            color_continuous_scale='Reds'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Análisis de tendencia anual
    st.write("#### Tendencia anual del déficit")
    
    # Agrupar por año y mes
    df.loc[:, "año_mes"] = df.index.strftime('%Y-%m')
    deficit_por_año_mes = df.groupby('año_mes')['deficit'].mean().reset_index()
    deficit_por_año_mes['año_mes'] = pd.to_datetime(deficit_por_año_mes['año_mes'] + '-01')
    
    # Crear gráfico
    fig = px.line(
        deficit_por_año_mes,
        x='año_mes',
        y='deficit',
        markers=True,
        labels={'año_mes': 'Año-Mes', 'deficit': 'Déficit (MW)'},
        title="Tendencia del déficit por año y mes"
    )
    
    fig.update_xaxes(
        dtick="M3",
        tickformat="%b\n%Y"
    )
    
    st.plotly_chart(fig, use_container_width=True)

def preparar_datos_detallados(df, filtro_año=None):
    """
    Prepara los datos para la visualización detallada, aplicando filtros si es necesario
    Args:
        df (pd.DataFrame): DataFrame con datos de déficit
        filtro_año (str, opcional): Año para filtrar los datos
    Returns:
        pd.DataFrame: DataFrame filtrado con datos detallados
    """
    df_filtrado = df.copy()
    
    # Filtrar por año si se especifica
    if filtro_año and filtro_año != "Todos los años":
        df_filtrado = df_filtrado[df_filtrado.index.year == int(filtro_año)]
    
    return df_filtrado

def mostrar_tabla_datos_detallados(df):
    """
    Muestra una tabla interactiva con los datos detallados de déficit
    Args:
        df (pd.DataFrame): DataFrame con datos de déficit filtrados
    """
    st.subheader("Datos Detallados del Período Seleccionado")
    
    if df.empty:
        st.warning("No hay datos disponibles para el período seleccionado.")
        return
    
    # Opciones de visualización
    col1, col2 = st.columns(2)
    with col1:
        mostrar_solo_deficit = st.checkbox(
            "Mostrar solo días con déficit", 
            value=False,
            key="mostrar_solo_deficit"
        )
    
    with col2:
        ordenar_por = st.selectbox(
            "Ordenar por",
            options=["Fecha (↑)", "Fecha (↓)", "Déficit (↑)", "Déficit (↓)"],
            key="ordenar_tabla_deficit"
        )
    
    # Aplicar filtros adicionales
    df_filtrado = df.copy()
    if mostrar_solo_deficit:
        df_filtrado = df_filtrado[df_filtrado["deficit"] > 0]
    
    # Aplicar ordenamiento
    if ordenar_por == "Fecha (↑)":
        df_filtrado = df_filtrado.sort_index(ascending=True)
    elif ordenar_por == "Fecha (↓)":
        df_filtrado = df_filtrado.sort_index(ascending=False)
    elif ordenar_por == "Déficit (↑)":
        df_filtrado = df_filtrado.sort_values("deficit", ascending=True)
    elif ordenar_por == "Déficit (↓)":
        df_filtrado = df_filtrado.sort_values("deficit", ascending=False)
    
    # Reindexar para mostrar la fecha como columna
    df_mostrar = df_filtrado.reset_index()
    
    # Formatear la fecha para mejor visualización
    df_mostrar["fecha"] = df_mostrar["fecha"].dt.strftime("%Y-%m-%d")
    
    # Seleccionar columnas a mostrar
    columnas_mostrar = [
        "fecha", "deficit", "porcentaje_deficit", "demanda", 
        "cant_plantas_averia", "impacto_motores_mw", "año", "mes", "dia_semana"
    ]
    
    # Filtrar columnas disponibles
    columnas_disponibles = [col for col in columnas_mostrar if col in df_mostrar.columns]
    
    # Cambiar nombres para mejor visualización
    nombres_columnas = {
        "fecha": "Fecha",
        "deficit": "Déficit (MW)",
        "porcentaje_deficit": "% de Déficit",
        "demanda": "Demanda (MW)",
        "cant_plantas_averia": "Plantas en Avería",
        "impacto_motores_mw": "Impacto Motores (MW)",
        "año": "Año",
        "mes": "Mes",
        "dia_semana": "Día"
    }
    
    # Mostrar DataFrame
    st.write(f"Mostrando {len(df_mostrar)} registros")
    st.dataframe(df_mostrar[columnas_disponibles].rename(columns={c: nombres_columnas.get(c, c) for c in columnas_disponibles}), use_container_width=True)
    
    # Botón para descargar datos
    csv = df_mostrar.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Descargar datos como CSV",
        data=csv,
        file_name=f"deficit_energetico_filtrado.csv",
        mime="text/csv",
        key="descargar_csv_deficit"
    )

def app():
    """
    Función principal del módulo de análisis de déficit
    """
    st.header("Análisis Histórico del Déficit Energético")
    st.markdown("---")
    
    # Cargar datos
    entradas = cargar_datos()
    
    # Verificar que se cargaron los datos correctamente
    if not entradas:
        st.error("No se pudieron cargar los datos. Verifique la ruta de los archivos.")
        return
    
    # Preparar dataframe específico para análisis de déficit
    df_completo = preparar_dataframe_deficit(entradas)
    
    if df_completo.empty:
        st.error("No hay datos disponibles para analizar.")
        return
    
    # Añadir selector de fechas al inicio
    st.write("### Selecciona el rango de fechas a analizar")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        fecha_inicio = st.date_input(
            "Fecha de inicio",
            value=df_completo.index.min().date(),
            min_value=df_completo.index.min().date(),
            max_value=df_completo.index.max().date(),
            key="fecha_inicio_deficit"
        )
    
    with col2:
        fecha_fin = st.date_input(
            "Fecha de fin",
            value=df_completo.index.max().date(),
            min_value=df_completo.index.min().date(),
            max_value=df_completo.index.max().date(),
            key="fecha_fin_deficit"
        )
    
    with col3:
        if st.button("Ver todo", key="ver_todo_deficit"):
            fecha_inicio = df_completo.index.min().date()
            fecha_fin = df_completo.index.max().date()
            st.experimental_rerun()
    
    # Filtrar dataframe según el rango de fechas seleccionado
    inicio_dt = datetime.combine(fecha_inicio, datetime.min.time())
    fin_dt = datetime.combine(fecha_fin, datetime.max.time())
    
    # Filtrar el dataframe para el rango seleccionado
    df = df_completo[(df_completo.index >= inicio_dt) & (df_completo.index <= fin_dt)]
    
    if df.empty:
        st.warning("No hay datos disponibles para el rango de fechas seleccionado.")
        return
    
    # Mostrar gráfico principal de déficit con línea de media
    st.write("### Déficit energético en el período seleccionado")
    
    # Filtrar valores nulos para cálculos
    df_deficit_no_nulo = df[df["deficit"].notnull()]
    
    # Calcular la media del déficit
    deficit_medio = df_deficit_no_nulo['deficit'].mean() if not df_deficit_no_nulo.empty else 0
    
    # Crear gráfico
    fig = go.Figure()
    
    # Añadir línea de déficit
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['deficit'],
        mode='lines',
        name='Déficit (MW)',
        line=dict(color='red', width=2)
    ))
    
    # Añadir línea de media
    fig.add_trace(go.Scatter(
        x=[df.index.min(), df.index.max()],
        y=[deficit_medio, deficit_medio],
        mode='lines',
        name=f'Media: {deficit_medio:.1f} MW',
        line=dict(color='black', width=1, dash='dash')
    ))
    
    # Configurar diseño
    fig.update_layout(
        title=f"Evolución del déficit energético ({fecha_inicio} a {fecha_fin})",
        xaxis_title="Fecha",
        yaxis_title="Déficit (MW)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Crear pestañas para cada tipo de análisis
    tab1, tab2, tab3, tab4 = st.tabs([
        "Estadísticas", 
        "Relación con Plantas", 
        "Distribución Temporal",
        "Datos Detallados"
    ])
    
    with tab1:
        # Mostrar estadísticas del período seleccionado
        mostrar_indicadores_deficit(df)
        
        # Análisis por días de la semana
        st.subheader("Déficit por día de la semana")
        
        # Agrupar por día de la semana
        dias_semana_orden = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        dias_semana_es = {
            "Monday": "Lunes",
            "Tuesday": "Martes",
            "Wednesday": "Miércoles",
            "Thursday": "Jueves",
            "Friday": "Viernes", 
            "Saturday": "Sábado",
            "Sunday": "Domingo"
        }
        
        # Convertir a día de la semana
        if "dia_semana" not in df.columns:
            df["dia_semana"] = df.index.strftime('%A')  # Día de la semana en inglés
            
        # Análisis por mes
        st.subheader("Déficit por mes")
        
        # Añadir columna de mes si no existe
        if "mes_num" not in df.columns:
            df["mes_num"] = df.index.month
            df["mes_nombre"] = df.index.strftime('%B')  # Nombre del mes
        
        # Definir nombres de meses en español
        meses_es = {
            "January": "Enero",
            "February": "Febrero",
            "March": "Marzo",
            "April": "Abril",
            "May": "Mayo",
            "June": "Junio",
            "July": "Julio",
            "August": "Agosto",
            "September": "Septiembre",
            "October": "Octubre",
            "November": "Noviembre",
            "December": "Diciembre"
        }
        
        # Calcular promedio de déficit por mes
        deficit_por_mes = df.groupby('mes_num')['deficit'].mean()
        
        # Crear lista de meses en orden
        meses_orden = list(range(1, 13))
        
        # Reindexar para mostrar todos los meses en orden
        deficit_por_mes = deficit_por_mes.reindex(meses_orden)
        
        # Crear gráfico de barras
        fig_meses = px.bar(
            x=[meses_es.get(datetime(2022, m, 1).strftime('%B'), datetime(2022, m, 1).strftime('%B')) for m in meses_orden], 
            y=deficit_por_mes.values,
            labels={'x': 'Mes', 'y': 'Déficit promedio (MW)'},
            title='Déficit promedio por mes',
            color=deficit_por_mes.values,
            color_continuous_scale='Reds',
        )
        
        # Mejorar diseño
        fig_meses.update_layout(
            xaxis_title="Mes",
            yaxis_title="Déficit promedio (MW)",
            height=400
        )
        
        st.plotly_chart(fig_meses, use_container_width=True)
    
    with tab2:
        # Análisis de plantas y relación con déficit
        analizar_plantas_deficit(entradas, df)
    
    with tab3:
        # Análisis de distribución temporal del déficit
        analizar_distribucion_temporal_deficit(df)
    
    with tab4:
        # Tabla detallada de datos
        mostrar_tabla_datos_detallados(df)