import os
import json
import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, date
import altair as alt

# Función para cargar todos los datos
def cargar_datos():
    base_dir = os.path.dirname(__file__)
    ruta = os.path.join(base_dir, os.pardir, "data", "processed", "datos_electricos_organizados.json")
    with open(ruta, "r", encoding="utf-8") as f:
        raw = json.load(f)
    entradas = []
    for anio in raw:
        for mes in raw[anio]:
            for rec in raw[anio][mes]:                
                dt = datetime.fromisoformat(rec["fecha"])
                enlace = rec.get("enlace", "")
                entradas.append({"fecha": dt, "datos": rec["datos"], "enlace": enlace})
    return eliminar_dias_repetidos(entradas)

# Función para eliminar días repetidos
def eliminar_dias_repetidos(entradas):
    vistos = set()
    unicas = []
    for e in entradas:
        d = e["fecha"].date()
        if d not in vistos:
            vistos.add(d)
            unicas.append(e)
    return unicas

# Función para preparar dataframe básico
def preparar_dataframe_basico(entradas):
    filas = []
    for e in entradas:
        pred = e["datos"].get("prediccion", {})
        filas.append({
            "fecha": e["fecha"],
            "afectacion": pred.get("afectacion"),
            "disponibilidad": pred.get("disponibilidad"),
            "demanda": pred.get("demanda_maxima"),
            "deficit": pred.get("deficit"),
            "respaldo": pred.get("respaldo")
        })
    return pd.DataFrame(filas).set_index("fecha").sort_index()

# Preparar datos para energía solar
def preparar_datos_solares(entradas):
    filas = []
    for e in entradas:
        d = e["fecha"]
        sol = e["datos"].get("paneles_solares", {})
        filas.append({
            "fecha": d, 
            "produccion_mwh": sol.get("produccion_mwh"),
            "parques": sol.get("cantidad_parques"),
            "capacidad_instalada": sol.get("capacidad_instalada")
        })
    return pd.DataFrame(filas).set_index("fecha").sort_index()

# Importar el estandarizador de nombres de plantas
from plant_standardizer import get_canonical_plant_name

# Obtener lista de plantas
def obtener_plantas(entradas):
    plantas = set()
    for e in entradas:
        pls = e["datos"].get("plantas", {})
        for clave in ("averia", "mantenimiento"):
            for p in pls.get(clave, []):
                nombre = p.get("planta")
                if nombre:
                    # Estandarizar el nombre de la planta
                    nombre_canonico = get_canonical_plant_name(nombre)
                    # Solo añadir nombres válidos (no None)
                    if nombre_canonico is not None:
                        plantas.add(nombre_canonico)
    return sorted(plantas)

# Función para obtener datos de estado de plantas
def datos_estado_plantas(entradas):
    filas = []
    for e in entradas:
        pls = e["datos"].get("plantas", {})
        fecha = e["fecha"]
          # Plantas en avería
        for p in pls.get("averia", []):
            nombre = p.get("planta")
            if nombre:
                # Estandarizar el nombre de la planta
                nombre_canonico = get_canonical_plant_name(nombre)
                # Solo añadir nombres válidos (no None)
                if nombre_canonico is not None:
                    filas.append({
                        "fecha": fecha,
                        "planta": nombre_canonico,
                        "estado": "Avería"
                    })
          # Plantas en mantenimiento
        for p in pls.get("mantenimiento", []):
            nombre = p.get("planta")
            if nombre:
                # Estandarizar el nombre de la planta
                nombre_canonico = get_canonical_plant_name(nombre)
                # Solo añadir nombres válidos (no None)
                if nombre_canonico is not None:
                    filas.append({
                        "fecha": fecha,
                        "planta": nombre_canonico,
                        "estado": "Mantenimiento"
                    })
    
    return pd.DataFrame(filas)

# Función para extraer métricas clave
def obtener_metricas_clave(entradas):
    ultimo_registro = max(entradas, key=lambda x: x["fecha"])
    datos = ultimo_registro["datos"]
    pred = datos.get("prediccion", {})
    
    return {
        "fecha": ultimo_registro["fecha"],
        "afectacion": pred.get("afectacion"),
        "disponibilidad": pred.get("disponibilidad"),
        "demanda_maxima": pred.get("demanda_maxima"),
        "deficit": pred.get("deficit"),
        "respaldo": pred.get("respaldo")
    }

# Función para crear gráficos interactivos con altair
def crear_grafico_temporal(df, y_column, color_column=None, title=None):
    if color_column:
        chart = alt.Chart(df.reset_index()).mark_line().encode(
            x=alt.X('fecha:T', title='Fecha'),
            y=alt.Y(f'{y_column}:Q', title=y_column.capitalize()),
            color=alt.Color(f'{color_column}:N'),
            tooltip=['fecha:T', f'{y_column}:Q', f'{color_column}:N']
        ).interactive()
    else:
        chart = alt.Chart(df.reset_index()).mark_line().encode(
            x=alt.X('fecha:T', title='Fecha'),
            y=alt.Y(f'{y_column}:Q', title=y_column.capitalize()),
            tooltip=['fecha:T', f'{y_column}:Q']
        ).interactive()
    
    if title:
        chart = chart.properties(title=title)
        
    return chart

# Función para crear gráficos de heatmap
def crear_heatmap(df, x_column, y_column, color_column, title=None):
    chart = alt.Chart(df).mark_rect().encode(
        x=alt.X(f'{x_column}:O', title=x_column.capitalize()),
        y=alt.Y(f'{y_column}:O', title=y_column.capitalize()),
        color=alt.Color(f'{color_column}:Q', scale=alt.Scale(scheme='viridis')),
        tooltip=[f'{x_column}:O', f'{y_column}:O', f'{color_column}:Q']
    ).interactive()
    
    if title:
        chart = chart.properties(title=title)
        
    return chart

# Función para mostrar KPIs
def mostrar_kpis(metricas):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Afectación", 
            f"{metricas['afectacion']} MW" if metricas['afectacion'] is not None else "N/A",
            delta=None
        )
        
    with col2:
        st.metric(
            "Disponibilidad", 
            f"{metricas['disponibilidad']} MW" if metricas['disponibilidad'] is not None else "N/A",
            delta=None
        )
        
    with col3:
        st.metric(
            "Déficit", 
            f"{metricas['deficit']} MW" if metricas['deficit'] is not None else "N/A",
            delta=None
        )

# Función para analizar tendencias
def analizar_tendencia(df, columna):
    """Analiza la tendencia de una columna de datos y devuelve un resumen"""
    if df.empty or columna not in df.columns:
        return "No hay datos suficientes para analizar tendencias"
    
    # Eliminar valores nulos
    serie = df[columna].dropna()
    
    if len(serie) < 2:
        return "No hay datos suficientes para analizar tendencias"
    
    # Calcular cambio porcentual y promedio
    cambio_abs = serie.iloc[-1] - serie.iloc[0]
    cambio_porc = (cambio_abs / serie.iloc[0]) * 100 if serie.iloc[0] != 0 else float('inf')
    promedio = serie.mean()
    
    # Determinar dirección de tendencia
    if cambio_abs > 0:
        direccion = "ascendente"
    elif cambio_abs < 0:
        direccion = "descendente"
    else:
        direccion = "estable"
    
    # Verificar volatilidad
    std_dev = serie.std()
    coef_var = (std_dev / promedio) * 100 if promedio != 0 else float('inf')
    
    if coef_var < 10:
        volatilidad = "baja"
    elif coef_var < 25:
        volatilidad = "moderada"
    else:
        volatilidad = "alta"
    
    return f"Tendencia {direccion} con volatilidad {volatilidad}. Cambio de {cambio_abs:.2f} MW ({cambio_porc:.1f}%) en el período analizado."

# Función para crear paletas de colores personalizadas
def get_color_palette(n_colors=3, palette_type="sequential"):
    if palette_type == "sequential":
        return alt.Scale(scheme='blues')
    elif palette_type == "diverging":
        return alt.Scale(scheme='redblue')
    else:  # categorical
        return alt.Scale(scheme='category10')
