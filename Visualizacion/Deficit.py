import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
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
        
        # Calcular el porcentaje del déficit respecto a la demanda
        deficit = pred.get("deficit")
        demanda = pred.get("demanda_maxima")
        porcentaje_deficit = ((deficit / demanda) * 100) if deficit is not None and demanda and demanda > 0 else None
        
        # Obtener el máximo impacto reportado
        maximo_impacto = impacto.get("maximo", {}).get("mw") if impacto else None
        
        # Contar plantas en avería
        plantas_averia = e["datos"].get("plantas", {}).get("averia", [])
        cant_plantas_averia = len([p for p in plantas_averia if p.get("planta")])
        
        # Motores fuera de servicio
        motores_con_problemas = e["datos"].get("distribuida", {}).get("motores_con_problemas", {})
        impacto_motores_mw = motores_con_problemas.get("impacto_mw")
        
        filas.append({
            "fecha": e["fecha"],
            "afectacion": pred.get("afectacion"),
            "disponibilidad": pred.get("disponibilidad"),
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
    st.subheader("Indicadores de Déficit Energético")
    
    # Filtrar valores no nulos para cálculos
    df_deficit_no_nulo = df[df["deficit"].notnull()]
    
    if df_deficit_no_nulo.empty:
        st.error("No hay datos suficientes para calcular indicadores de déficit.")
        return
    
    # Obtener métricas principales
    ultimo_dia = df_deficit_no_nulo.index.max()
    deficit_actual = df_deficit_no_nulo.loc[ultimo_dia, "deficit"]
    
    # Cálculos principales
    metricas = calcular_metricas_deficit(df_deficit_no_nulo, ultimo_dia)
    
    # Mostrar KPIs en columnas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Déficit Actual (MW)",
            value=f"{int(deficit_actual)}" if deficit_actual is not None else "N/D",
            delta=f"{int(metricas['delta_deficit'])}" if metricas['delta_deficit'] is not None else None,
            delta_color="inverse" if metricas['delta_deficit'] and metricas['delta_deficit'] > 0 else "normal"
        )
        
        st.metric(
            label="Déficit Promedio (MW)",
            value=f"{int(metricas['deficit_promedio'])}" if metricas['deficit_promedio'] is not None else "N/D"
        )
    
    with col2:
        st.metric(
            label="Var. vs Semana Anterior",
            value=f"{int(metricas['delta_semanal'])}" if metricas['delta_semanal'] is not None else "N/D",
            delta=f"{int(metricas['delta_semanal'])}" if metricas['delta_semanal'] is not None else None,
            delta_color="inverse" if metricas['delta_semanal'] and metricas['delta_semanal'] > 0 else "normal"
        )
        
        st.metric(
            label="Déficit Máximo (MW)",
            value=f"{int(metricas['deficit_maximo'])}" if metricas['deficit_maximo'] is not None else "N/D",
            help=f"Registrado el {metricas['fecha_deficit_maximo']}"
        )
    
    with col3:
        st.metric(
            label="% de la Demanda",
            value=f"{metricas['porcentaje_deficit_actual']:.1f}%" if metricas['porcentaje_deficit_actual'] is not None else "N/D"
        )
        
        st.metric(
            label="Déficit Mínimo (MW)",
            value=f"{int(metricas['deficit_minimo'])}" if metricas['deficit_minimo'] is not None else "N/D"
        )
    
    with col4:
        st.metric(
            label="Días con Déficit (Último Mes)",
            value=f"{metricas['dias_con_deficit_ultimo_mes']}/{min(30, metricas['dias_ultimo_mes'])}"
        )
        
        st.metric(
            label="% Días con Déficit (Total)",
            value=f"{metricas['porcentaje_dias_con_deficit']:.1f}%",
            help=f"{metricas['dias_con_deficit']} días de {metricas['total_dias_datos']} analizados"
        )

def calcular_metricas_deficit(df_deficit_no_nulo, ultimo_dia):
    """
    Calcula las métricas principales para el análisis de déficit
    Args:
        df_deficit_no_nulo (pd.DataFrame): DataFrame filtrado sin valores nulos
        ultimo_dia (datetime): Fecha del último registro
    Returns:
        dict: Diccionario con todas las métricas calculadas
    """
    metricas = {}
    
    # Métricas básicas
    metricas['deficit_actual'] = df_deficit_no_nulo.loc[ultimo_dia, "deficit"]
    metricas['deficit_promedio'] = df_deficit_no_nulo["deficit"].mean()
    metricas['deficit_maximo'] = df_deficit_no_nulo["deficit"].max()
    metricas['deficit_minimo'] = df_deficit_no_nulo["deficit"].min()
    metricas['fecha_deficit_maximo'] = df_deficit_no_nulo["deficit"].idxmax().strftime("%d/%m/%Y")
    
    # Cálculos de variación
    try:
        dia_anterior = df_deficit_no_nulo.index[df_deficit_no_nulo.index < ultimo_dia].max()
        deficit_dia_anterior = df_deficit_no_nulo.loc[dia_anterior, "deficit"]
        metricas['delta_deficit'] = metricas['deficit_actual'] - deficit_dia_anterior
    except:
        metricas['delta_deficit'] = None
    
    try:
        semana_anterior = ultimo_dia - timedelta(days=7)
        deficit_semana_anterior = df_deficit_no_nulo.loc[semana_anterior:semana_anterior + timedelta(days=1), "deficit"].iloc[0]
        metricas['delta_semanal'] = metricas['deficit_actual'] - deficit_semana_anterior
    except:
        metricas['delta_semanal'] = None
    
    # Métricas de porcentaje y días
    metricas['porcentaje_deficit_actual'] = df_deficit_no_nulo.loc[ultimo_dia, "porcentaje_deficit"]
    
    ultimo_mes = ultimo_dia - timedelta(days=30)
    df_ultimo_mes = df_deficit_no_nulo[df_deficit_no_nulo.index >= ultimo_mes]
    
    metricas['dias_con_deficit_ultimo_mes'] = (df_ultimo_mes["deficit"] > 0).sum()
    metricas['dias_ultimo_mes'] = df_ultimo_mes.shape[0]
    
    metricas['total_dias_datos'] = df_deficit_no_nulo.shape[0]
    metricas['dias_con_deficit'] = (df_deficit_no_nulo["deficit"] > 0).sum()
    metricas['porcentaje_dias_con_deficit'] = (metricas['dias_con_deficit'] / metricas['total_dias_datos'] * 100)
    
    return metricas

def mostrar_grafico_tendencia(df):
    """
    Muestra un gráfico de tendencia interactivo del déficit energético
    Args:
        df (pd.DataFrame): DataFrame con datos de déficit procesados
    """
    st.subheader("Evolución Histórica del Déficit Energético")
    
    # Añadir filtros de tiempo
    col1, col2 = st.columns([1, 3])
    
    # Configuración de filtros
    config_grafico = configurar_filtros_tendencia(df, col1)
    
    if not config_grafico['anos_seleccionados'] and not config_grafico.get('periodo_personalizado'):
        st.warning("Por favor, seleccione un período para visualizar.")
        return
        
    # Preparar datos filtrados
    df_filtrado = preparar_datos_tendencia(df, config_grafico)
    
    if df_filtrado.empty:
        st.warning("No hay datos para el periodo seleccionado.")
        return
        
    # Crear y mostrar gráfico
    fig = crear_grafico_tendencia(df_filtrado, config_grafico)
    st.plotly_chart(fig, use_container_width=True)
    
    # Mostrar estadísticas adicionales
    mostrar_estadisticas_tendencia(df_filtrado)

def configurar_filtros_tendencia(df, col):
    """
    Configura los filtros para el gráfico de tendencia
    """
    config = {}
    
    # Filtro de tipo de selección
    tipo_filtro = col.radio(
        "Tipo de filtro",
        ["Por año", "Por rango de fechas"],
        key="tipo_filtro_tendencia"
    )
    
    if tipo_filtro == "Por año":
        # Filtros temporales por año
        anos = sorted(df.index.year.unique())
        if not anos:
            return None
                
        config['anos_seleccionados'] = col.multiselect(
            "Seleccione años",
            options=anos,
            default=[max(anos)],
            key="anos_tendencia"
        )
        config['periodo_personalizado'] = False
    else:
        # Filtro por rango de fechas personalizado
        fecha_inicio, fecha_fin = col.date_input(
            "Rango de fechas a analizar",
            value=[df.index.min().date(), df.index.max().date()],
            min_value=df.index.min().date(),
            max_value=df.index.max().date(),
            key="rango_fechas_tendencia"
        )
        config['fecha_inicio'] = fecha_inicio
        config['fecha_fin'] = fecha_fin
        config['periodo_personalizado'] = True
        config['anos_seleccionados'] = []
    
    config['periodo'] = col.radio(
        "Agregación de datos",
        ["Diario", "Semanal", "Mensual"],
        index=0,
        key="periodo_tendencia"
    )
    
    # Opciones de visualización
    col.markdown("#### Opciones de visualización")
    config['mostrar_promedio'] = col.checkbox("Mostrar promedio móvil", value=True, key="mostrar_promedio")
    config['mostrar_disponibilidad'] = col.checkbox("Mostrar disponibilidad", value=False, key="mostrar_disponibilidad")
    config['mostrar_demanda'] = col.checkbox("Mostrar demanda", value=False, key="mostrar_demanda")
    
    return config

def preparar_datos_tendencia(df, config):
    """
    Prepara los datos para el gráfico de tendencia según la configuración
    """
    # Filtrar datos según tipo de filtro
    if config.get('periodo_personalizado', False):
        # Filtrar por rango de fechas personalizado
        fecha_inicio_dt = datetime.combine(config['fecha_inicio'], datetime.min.time())
        fecha_fin_dt = datetime.combine(config['fecha_fin'], datetime.max.time())
        df_filtrado = df[(df.index >= fecha_inicio_dt) & (df.index <= fecha_fin_dt)]
    else:
        # Filtrar por años seleccionados
        df_filtrado = df[df.index.year.isin(config['anos_seleccionados'])] if config['anos_seleccionados'] else df.copy()
    
    if df_filtrado.empty:
        return pd.DataFrame()
    
    # Establecer columnas a mostrar
    columnas_a_mostrar = ["deficit"]
    if config['mostrar_disponibilidad']:
        columnas_a_mostrar.append("disponibilidad")
    if config['mostrar_demanda']:
        columnas_a_mostrar.append("demanda")
    
    # Aplicar resample según periodo
    if config['periodo'] == "Semanal":
        df_resample = df_filtrado[columnas_a_mostrar].resample('W').mean()
    elif config['periodo'] == "Mensual":
        df_resample = df_filtrado[columnas_a_mostrar].resample('M').mean()
    else:  # Diario
        df_resample = df_filtrado[columnas_a_mostrar]
    
    return df_resample

def crear_grafico_tendencia(df_resample, config):
    """
    Crea el gráfico de tendencia según los datos y configuración
    """
    # Preparar datos para el gráfico
    df_plot = df_resample.reset_index()
    columnas_a_mostrar = df_resample.columns
    nombres_columnas = [
        "Déficit (MW)" if col == "deficit" else
        "Disponibilidad (MW)" if col == "disponibilidad" else
        "Demanda (MW)" if col == "demanda" else col
        for col in columnas_a_mostrar
    ]
    
    df_plot = df_plot.melt(
        id_vars=["fecha"], 
        value_vars=columnas_a_mostrar,
        var_name="Variable",
        value_name="Valor"
    )
    
    # Mapear nombres de variables
    mapeo_nombres = dict(zip(columnas_a_mostrar, nombres_columnas))
    df_plot["Variable"] = df_plot["Variable"].map(lambda x: mapeo_nombres.get(x, x))
    
    # Crear gráfico base
    titulo_periodo = "Promedio Mensual" if config['periodo'] == "Mensual" else \
                    "Promedio Semanal" if config['periodo'] == "Semanal" else \
                    "Valores Diarios"
    
    fig = px.line(
        df_plot,
        x="fecha",
        y="Valor",
        color="Variable",
        title=f"Evolución del Déficit Energético - {titulo_periodo}",
        labels={"fecha": "Fecha", "Valor": "MW"},
        template="plotly_white"
    )
    
    # Añadir promedio móvil si se solicita
    if config['mostrar_promedio'] and "deficit" in columnas_a_mostrar:
        agregar_promedios_moviles(fig, df_resample, config)
    
    # Personalizar diseño
    personalizar_diseno_grafico(fig)
    
    return fig

def agregar_promedios_moviles(fig, df_resample, config):
    """
    Agrega las líneas de promedio móvil al gráfico
    """
    df_deficit = df_resample[["deficit"]].sort_index()
    df_deficit["MA_7"] = df_deficit["deficit"].rolling(window=7, min_periods=1).mean()
    df_deficit["MA_30"] = df_deficit["deficit"].rolling(window=30, min_periods=1).mean()
    
    fig.add_trace(
        go.Scatter(
            x=df_deficit.index,
            y=df_deficit["MA_7"],
            mode="lines",
            line=dict(width=2, color="#FF8C00", dash="dash"),
            name="Promedio 7 días"
        )
    )
    
    if config['periodo'] != "Mensual":
        fig.add_trace(
            go.Scatter(
                x=df_deficit.index,
                y=df_deficit["MA_30"],
                mode="lines",
                line=dict(width=2.5, color="#B22222", dash="dot"),
                name="Promedio 30 días"
            )
        )

def personalizar_diseno_grafico(fig):
    """
    Personaliza el diseño del gráfico
    """
    fig.update_layout(
        height=500,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode="x unified",
        xaxis=dict(
            rangeslider=dict(visible=True),
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=3, label="3m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(step="all")
                ])
            )
        )
    )
    
def mostrar_estadisticas_tendencia(df_filtrado):
    """
    Muestra estadísticas detalladas del periodo seleccionado
    """
    if df_filtrado.empty:
        return
        
    with st.expander("Ver estadísticas detalladas"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Déficit promedio", f"{df_filtrado['deficit'].mean():.2f} MW")
            st.metric("Días con déficit", f"{(df_filtrado['deficit'] > 0).sum()}")
        
        with col2:
            st.metric("Déficit máximo", f"{df_filtrado['deficit'].max():.2f} MW")
            st.metric("Fecha déficit máximo", df_filtrado['deficit'].idxmax().strftime("%d/%m/%Y"))
        
        with col3:
            if 'porcentaje_deficit' in df_filtrado.columns:
                st.metric("Porcentaje promedio de déficit", f"{df_filtrado['porcentaje_deficit'].mean():.2f}%")
                st.metric("Porcentaje máximo de déficit", f"{df_filtrado['porcentaje_deficit'].max():.2f}%")

def analizar_plantas_deficit(entradas, df):
    """
    Proporciona un análisis detallado de las plantas en avería y su relación con el déficit
    Args:
        entradas (list): Lista de registros de datos eléctricos
        df (pd.DataFrame): DataFrame con datos de déficit procesados
    """
    st.subheader("Análisis de Plantas en Avería y su Impacto en el Déficit")
    
    # Obtener datos de plantas y validar
    df_plantas = datos_estado_plantas(entradas)
    plantas_list = obtener_plantas(entradas)
    
    if not plantas_list:
        st.warning("No hay datos de plantas disponibles.")
        return
    
    # Configurar interfaz de selección y filtros
    config = configurar_filtros_plantas(df, plantas_list)
    
    # Procesar datos según filtros
    df_analisis = procesar_datos_plantas(df, df_plantas, config)
    
    if df_analisis['df_filtrado'].empty:
        st.error("No hay datos para el rango de fechas seleccionado.")
        return
    
    # Mostrar análisis
    mostrar_analisis_plantas(df_analisis, config)

def configurar_filtros_plantas(df, plantas_list):
    """
    Configura los filtros para el análisis de plantas
    """
    col1, col2 = st.columns([1, 2])
    config = {}
    
    with col1:
        config['planta_seleccionada'] = st.selectbox(
            "Seleccionar planta para análisis",
            options=["Todas las plantas"] + plantas_list,
            key="plantas_deficit_selectbox"
        )
        
        config['fechas'] = st.date_input(
            "Rango de fechas",
            value=[df.index.min().date(), df.index.max().date()],
            min_value=df.index.min().date(),
            max_value=df.index.max().date(),
            key="fechas_plantas_deficit"
        )
        
        config['mostrar_correlacion'] = st.checkbox("Mostrar correlación con déficit", value=True, key="mostrar_correlacion_deficit")
    
    return config

def procesar_datos_plantas(df, df_plantas, config):
    """
    Procesa los datos de plantas según la configuración de filtros
    """
    fecha_inicio = config['fechas'][0]
    fecha_fin = config['fechas'][1]
    fecha_inicio_dt = datetime.combine(fecha_inicio, datetime.min.time())
    fecha_fin_dt = datetime.combine(fecha_fin, datetime.max.time())
    
    # Filtrar datos principales
    df_filtrado = df[(df.index >= fecha_inicio_dt) & (df.index <= fecha_fin_dt)]
    
    # Filtrar datos de plantas
    df_plantas_filtrado = df_plantas[
        (df_plantas["fecha"] >= fecha_inicio_dt) &
        (df_plantas["fecha"] <= fecha_fin_dt)
    ]
    
    if config['planta_seleccionada'] != "Todas las plantas":
        df_plantas_filtrado = df_plantas_filtrado[df_plantas_filtrado["planta"] == config['planta_seleccionada']]
    
    return {
        'df_filtrado': df_filtrado,
        'df_plantas_filtrado': df_plantas_filtrado
    }

def mostrar_analisis_plantas(df_analisis, config):
    """
    Muestra el análisis detallado de plantas
    """
    df_filtrado = df_analisis['df_filtrado']
    df_plantas_filtrado = df_analisis['df_plantas_filtrado']
    
    # Análisis de frecuencia
    df_freq = df_plantas_filtrado.groupby("planta")["fecha"].agg(['count']).sort_values('count', ascending=False)
    df_freq = df_freq.rename(columns={'count': 'días_en_avería'})
    
    # Mostrar opciones de visualización
    vista_seleccionada = st.radio(
        "Tipo de visualización:",
        ["Tabla de frecuencias", "Gráfico de barras"],
        key="vista_analisis_plantas"
    )
    
    # Mostrar visualización según selección
    if not df_freq.empty:
        if vista_seleccionada == "Tabla de frecuencias":
            st.write("Frecuencia de averías por planta:")
            st.dataframe(df_freq.style.background_gradient(cmap='YlOrRd'))
        else:
            # Preparar datos para gráfico
            df_graph = df_freq.reset_index().sort_values('días_en_avería', ascending=True).tail(10)
            fig = px.bar(
                df_graph,
                x='días_en_avería',
                y='planta',
                title="Top 10 plantas con más días en avería",
                labels={'días_en_avería': 'Días en avería', 'planta': 'Planta'},
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Análisis de correlación si está habilitado
    if config['mostrar_correlacion']:
        mostrar_correlacion_deficit_averias(df_filtrado, df_plantas_filtrado)

def mostrar_correlacion_deficit_averias(df_filtrado, df_plantas_filtrado):
    """
    Muestra la correlación entre déficit y averías
    """
    # Contar averías por día
    averias_por_dia = df_plantas_filtrado.groupby("fecha").size().reindex(df_filtrado.index, fill_value=0)
    
    # Crear gráfico de correlación
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df_filtrado.index,
        y=df_filtrado["deficit"],
        name="Déficit (MW)",
        line=dict(color="red")
    ))
    
    fig.add_trace(go.Scatter(
        x=averias_por_dia.index,
        y=averias_por_dia,
        name="Cantidad de Plantas en Avería",
        line=dict(color="blue", dash="dot"),
        yaxis="y2"
    ))
    
    fig.update_layout(
        title="Correlación entre Déficit y Plantas en Avería",
        xaxis_title="Fecha",
        yaxis_title="Déficit (MW)",
        yaxis2=dict(
            title="Cantidad de Plantas",
            overlaying="y",
            side="right"
        ),
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)

def analizar_distribucion_deficit(df):
    """
    Analiza la distribución temporal del déficit energético
    """
    st.subheader("Distribución Temporal del Déficit")
    
    # Filtros para la distribución temporal
    col1, col2 = st.columns([1, 2])
    
    with col1:
        tipo_analisis = st.radio(
            "Tipo de análisis",
            ["Por día de semana", "Por mes", "Por año", "Distribución horaria"],
            key="tipo_analisis_dist"
        )
        
        # Filtrar rango de fechas
        fecha_inicio, fecha_fin = st.date_input(
            "Rango de fechas",
            value=[df.index.min().date(), df.index.max().date()],
            min_value=df.index.min().date(),
            max_value=df.index.max().date(),
            key="fechas_distribucion"
        )
        
        mostrar_porcentaje = st.checkbox("Mostrar como porcentaje", value=False, key="mostrar_porcentaje_dist")
    
    # Filtrar datos
    fecha_inicio_dt = datetime.combine(fecha_inicio, datetime.min.time())
    fecha_fin_dt = datetime.combine(fecha_fin, datetime.max.time())
    df_filtrado = df[(df.index >= fecha_inicio_dt) & (df.index <= fecha_fin_dt)]
    
    if df_filtrado.empty:
        st.warning("No hay datos para el rango de fechas seleccionado.")
        return
    
    # Ejecutar análisis según selección
    if tipo_analisis == "Por día de semana":
        analizar_por_dia_semana(df_filtrado, mostrar_porcentaje)
    elif tipo_analisis == "Por mes":
        analizar_por_mes(df_filtrado, mostrar_porcentaje)
    elif tipo_analisis == "Por año":
        analizar_por_ano(df_filtrado, mostrar_porcentaje)
    else:
        analizar_distribucion_horaria(df_filtrado, fecha_inicio, fecha_fin)

def analizar_por_dia_semana(df, mostrar_porcentaje):
    """
    Analiza el déficit por día de la semana
    """
    # Mapear los días de la semana para ordenarlos correctamente
    dias_semana = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    dias_esp = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    mapeo_dias = dict(zip(dias_semana, dias_esp))
    
    # Preparar datos
    df_dias = df.copy()
    df_dias['dia_semana_eng'] = df_dias.index.strftime('%A')
    df_dias['dia_semana'] = df_dias['dia_semana_eng'].map(mapeo_dias)
    
    # Agrupar datos
    if mostrar_porcentaje:
        df_agrupado = df_dias.groupby('dia_semana')['deficit'].mean()
    else:
        df_agrupado = df_dias.groupby('dia_semana')['deficit'].mean()
    
    # Ordenar por día de la semana
    df_plot = df_agrupado.reset_index()
    # Convertir a categoría ordenada
    df_plot['dia_semana'] = pd.Categorical(df_plot['dia_semana'], categories=dias_esp, ordered=True)
    df_plot = df_plot.sort_values('dia_semana')
    
    # Crear gráfico
    fig = px.bar(
        df_plot, 
        x='dia_semana', 
        y='deficit',
        title=f"Déficit promedio por día de la semana {'(%)' if mostrar_porcentaje else '(MW)'}",
        labels={
            'dia_semana': 'Día de la semana',
            'deficit': 'Déficit Promedio (%)'if mostrar_porcentaje else 'Déficit Promedio (MW)'
        }
    )
    
    st.plotly_chart(fig, use_container_width=True)

def analizar_por_mes(df, mostrar_porcentaje):
    """
    Analiza el déficit por mes
    """
    # Mapear los meses para ordenarlos correctamente
    meses_eng = ["January", "February", "March", "April", "May", "June", 
                "July", "August", "September", "October", "November", "December"]
    meses_esp = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    mapeo_meses = dict(zip(meses_eng, meses_esp))
    
    # Preparar datos
    df_meses = df.copy()
    df_meses['mes_eng'] = df_meses.index.strftime('%B')
    df_meses['mes'] = df_meses['mes_eng'].map(mapeo_meses)
    
    # Agrupar datos
    if mostrar_porcentaje:
        df_agrupado = df_meses.groupby('mes')['porcentaje_deficit'].mean()
    else:
        df_agrupado = df_meses.groupby('mes')['deficit'].mean()
    
    # Ordenar por mes
    df_plot = df_agrupado.reset_index()
    # Convertir a categoría ordenada
    df_plot['mes'] = pd.Categorical(df_plot['mes'], categories=meses_esp, ordered=True)
    df_plot = df_plot.sort_values('mes')
    
    # Crear gráfico
    y_col = 'porcentaje_deficit' if mostrar_porcentaje else 'deficit'
    titulo = f"Déficit promedio por mes {'(%)' if mostrar_porcentaje else '(MW)'}"
    y_label = 'Déficit Promedio (%)' if mostrar_porcentaje else 'Déficit Promedio (MW)'
    
    fig = px.bar(
        df_plot, 
        x='mes', 
        y=y_col,
        title=titulo,
        labels={
            'mes': 'Mes',
            y_col: y_label
        }
    )
    
    st.plotly_chart(fig, use_container_width=True)

def analizar_por_ano(df, mostrar_porcentaje):
    """
    Analiza el déficit por año
    """
    # Preparar datos
    df_anos = df.copy()
    df_anos['año'] = df_anos.index.year
    
    # Agrupar datos
    if mostrar_porcentaje:
        df_agrupado = df_anos.groupby('año')['porcentaje_deficit'].mean()
    else:
        df_agrupado = df_anos.groupby('año')['deficit'].mean()
    
    # Ordenar por año
    df_plot = df_agrupado.reset_index()
    df_plot = df_plot.sort_values('año')
    
    # Crear gráfico
    y_col = 'porcentaje_deficit' if mostrar_porcentaje else 'deficit'
    titulo = f"Déficit promedio por año {'(%)' if mostrar_porcentaje else '(MW)'}"
    y_label = 'Déficit Promedio (%)' if mostrar_porcentaje else 'Déficit Promedio (MW)'
    
    fig = px.bar(
        df_plot, 
        x='año', 
        y=y_col,
        title=titulo,
        labels={
            'año': 'Año',
            y_col: y_label
        }
    )
    
    st.plotly_chart(fig, use_container_width=True)

def analizar_distribucion_horaria(df, fecha_inicio, fecha_fin):
    """
    Analiza la distribución horaria del déficit
    """
    st.info("La distribución horaria del déficit no está disponible en los datos actuales.")
    st.write("Esta funcionalidad se implementará cuando se disponga de datos con resolución horaria.")

def app():
    """
    Función principal del módulo de análisis de déficit
    """
    st.header("Análisis Histórico del Déficit Energético")
    st.markdown("---")
    
    # Cargar datos
    entradas = cargar_datos()
    
    # Preparar dataframe específico para análisis de déficit
    df = preparar_dataframe_deficit(entradas)
    
    if df.empty:
        st.error("No hay datos disponibles para analizar.")
        return
    
    # Crear pestañas para cada tipo de análisis
    tab1, tab2, tab3, tab4 = st.tabs([
        "Indicadores y Tendencias", 
        "Relación con Plantas", 
        "Distribución Temporal",
        "Datos Detallados"
    ])
    
    with tab1:
        # Mostrar indicadores principales
        mostrar_indicadores_deficit(df)
        
        # Mostrar gráfico de tendencias
        mostrar_grafico_tendencia(df)
        
        # Añadir sección para comparar períodos específicos
        with st.expander("Comparar Períodos Específicos"):
            st.write("### Comparación de Períodos")
            
            # Seleccionar dos rangos de fechas para comparar
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("#### Primer Período")
                fecha_inicio1, fecha_fin1 = st.date_input(
                    "Rango de fechas (Período 1)",
                    value=[df.index.min().date(), (df.index.min() + timedelta(days=30)).date()],
                    min_value=df.index.min().date(),
                    max_value=df.index.max().date(),
                    key="fecha_periodo1"
                )
            
            with col2:
                st.write("#### Segundo Período")
                fecha_inicio2, fecha_fin2 = st.date_input(
                    "Rango de fechas (Período 2)",
                    value=[(df.index.max() - timedelta(days=30)).date(), df.index.max().date()],
                    min_value=df.index.min().date(),
                    max_value=df.index.max().date(),
                    key="fecha_periodo2"
                )
            
            # Convertir a datetime
            fecha_inicio1_dt = datetime.combine(fecha_inicio1, datetime.min.time())
            fecha_fin1_dt = datetime.combine(fecha_fin1, datetime.max.time())
            fecha_inicio2_dt = datetime.combine(fecha_inicio2, datetime.min.time())
            fecha_fin2_dt = datetime.combine(fecha_fin2, datetime.max.time())
            
            # Filtrar los periodos
            df_periodo1 = df[(df.index >= fecha_inicio1_dt) & (df.index <= fecha_fin1_dt)]
            df_periodo2 = df[(df.index >= fecha_inicio2_dt) & (df.index <= fecha_fin2_dt)]
            
            # Etiquetas para identificar los periodos
            p1_label = f"{fecha_inicio1.strftime('%d/%m/%Y')} - {fecha_fin1.strftime('%d/%m/%Y')}"
            p2_label = f"{fecha_inicio2.strftime('%d/%m/%Y')} - {fecha_fin2.strftime('%d/%m/%Y')}"
            
            # Verificar si hay datos suficientes
            if not df_periodo1.empty and not df_periodo2.empty:
                # Crear un DataFrame con días alineados para comparación
                # Usar un índice de días relativos (0, 1, 2...) para comparar períodos de diferente longitud
                df_p1_aligned = df_periodo1.reset_index().copy()
                df_p1_aligned["dia_relativo"] = range(len(df_p1_aligned))
                df_p1_aligned = df_p1_aligned[["dia_relativo", "deficit", "fecha"]]
                df_p1_aligned["periodo"] = "Período 1"
                
                df_p2_aligned = df_periodo2.reset_index().copy()
                df_p2_aligned["dia_relativo"] = range(len(df_p2_aligned))
                df_p2_aligned = df_p2_aligned[["dia_relativo", "deficit", "fecha"]]
                df_p2_aligned["periodo"] = "Período 2"
                
                # Combinar para graficar
                df_comparativo = pd.concat([df_p1_aligned, df_p2_aligned])
                
                # Crear gráfico comparativo
                fig = px.line(
                    df_comparativo,
                    x="dia_relativo",
                    y="deficit",
                    color="periodo",
                    hover_data=["fecha"],
                    labels={"deficit": "Déficit (MW)", "dia_relativo": "Día del Período"},
                    color_discrete_map={"Período 1": "#1E88E5", "Período 2": "#D81B60"},
                    markers=True
                )
                
                # Configuración del gráfico
                fig.update_layout(
                    title="Comparación de Déficit entre Períodos (Alineados por Día)",
                    xaxis_title="Fecha (Alineada)",
                    yaxis_title="Déficit (MW)",
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Mostrar tabla comparativa
                st.write("### Estadísticas comparativas")
                
                df_estadisticas = pd.DataFrame({
                    "Estadística": [
                        "Déficit Promedio (MW)",
                        "Déficit Máximo (MW)",
                        "Días con Déficit",
                        "Porcentaje de Déficit Promedio",
                        "Plantas en Avería (Promedio)"
                    ],
                    f"Período 1 ({p1_label})": [
                        f"{df_periodo1['deficit'].mean():.2f}",
                        f"{df_periodo1['deficit'].max():.2f}",
                        f"{(df_periodo1['deficit'] > 0).sum()}",
                        f"{df_periodo1['porcentaje_deficit'].mean():.2f}%",
                        f"{df_periodo1['cant_plantas_averia'].mean():.2f}"
                    ],
                    f"Período 2 ({p2_label})": [
                        f"{df_periodo2['deficit'].mean():.2f}",
                        f"{df_periodo2['deficit'].max():.2f}",
                        f"{(df_periodo2['deficit'] > 0).sum()}",
                        f"{df_periodo2['porcentaje_deficit'].mean():.2f}%",
                        f"{df_periodo2['cant_plantas_averia'].mean():.2f}"
                    ],
                    "Diferencia": [
                        f"{df_periodo2['deficit'].mean() - df_periodo1['deficit'].mean():.2f}",
                        f"{df_periodo2['deficit'].max() - df_periodo1['deficit'].max():.2f}",
                        f"{(df_periodo2['deficit'] > 0).sum() - (df_periodo1['deficit'] > 0).sum()}",
                        f"{df_periodo2['porcentaje_deficit'].mean() - df_periodo1['porcentaje_deficit'].mean():.2f}%",
                        f"{df_periodo2['cant_plantas_averia'].mean() - df_periodo1['cant_plantas_averia'].mean():.2f}"
                    ]
                })
                
                st.dataframe(df_estadisticas, use_container_width=True)
            else:
                st.warning("No hay datos suficientes para uno o ambos períodos seleccionados.")
    
    with tab2:
        # Análisis de plantas y relación con déficit
        analizar_plantas_deficit(entradas, df)
    
    with tab3:
        # Análisis de distribución del déficit
        analizar_distribucion_deficit(df)
    
    with tab4:
        # Tabla interactiva con datos detallados
        st.write("### Datos Detallados del Déficit Energético")
        st.write("#### Opciones de filtrado")
        
        # Filtro por año o por rango de fechas
        tipo_filtro_tabla = st.radio(
            "Filtrar por:",
            ["Año", "Rango de fechas"],
            key="tipo_filtro_tabla"
        )
        
        if tipo_filtro_tabla == "Año":
            # Filtro por año
            años = sorted(df.index.year.unique())
            año_seleccionado = st.selectbox(
                "Seleccionar año",
                options=["Todos los años"] + [str(año) for año in años],
                key="ano_tabla_deficit"
            )
            
            # Aplicar filtro por año
            if año_seleccionado != "Todos los años":
                df_filtrado = df[df.index.year == int(año_seleccionado)].copy()
            else:
                df_filtrado = df.copy()
        else:
            # Filtro por rango de fechas
            fecha_inicio, fecha_fin = st.date_input(
                "Rango de fechas",
                value=[df.index.min().date(), df.index.max().date()],
                min_value=df.index.min().date(),
                max_value=df.index.max().date(),
                key="rango_fechas_tabla_deficit"
            )
            
            # Aplicar filtro por rango de fechas
            fecha_inicio_dt = datetime.combine(fecha_inicio, datetime.min.time())
            fecha_fin_dt = datetime.combine(fecha_fin, datetime.max.time())
            df_filtrado = df[(df.index >= fecha_inicio_dt) & (df.index <= fecha_fin_dt)].copy()
        
        # Opciones adicionales de filtrado
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
            "fecha", "deficit", "porcentaje_deficit", "disponibilidad", "demanda", 
            "cant_plantas_averia", "impacto_motores_mw", "año", "mes"
        ]
        
        # Filtrar columnas disponibles
        columnas_disponibles = [col for col in columnas_mostrar if col in df_mostrar.columns]
        
        # Cambiar nombres para mejor visualización
        nombres_columnas = {
            "fecha": "Fecha",
            "deficit": "Déficit (MW)",
            "porcentaje_deficit": "% de Déficit",
            "disponibilidad": "Disponibilidad (MW)",
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
            file_name=f"deficit_energetico_{año_seleccionado if tipo_filtro_tabla == 'Año' and año_seleccionado != 'Todos los años' else 'filtrado'}.csv",
            mime="text/csv",
            key="descargar_csv_deficit"
        )
