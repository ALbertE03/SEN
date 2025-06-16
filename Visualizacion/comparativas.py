import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, date
from .utils import (
    cargar_datos, 
    preparar_dataframe_basico, 
    obtener_plantas,
    datos_estado_plantas
)

def crear_grafico_comparativo(df, col1, col2, titulo1, titulo2):
    """Crea un gráfico comparativo entre dos variables."""
    base = alt.Chart(df.reset_index())
    
    linea1 = base.mark_line(color='#5276A7').encode(
        x=alt.X('fecha:T', title='Fecha'),
        y=alt.Y(f'{col1}:Q', title=titulo1),
        tooltip=[
            alt.Tooltip('fecha:T', title='Fecha'),
            alt.Tooltip(f'{col1}:Q', title=titulo1)
        ]
    )
    
    linea2 = base.mark_line(color='#57A44C').encode(
        x=alt.X('fecha:T'),
        y=alt.Y(f'{col2}:Q', title=titulo2),
        tooltip=[
            alt.Tooltip('fecha:T', title='Fecha'),
            alt.Tooltip(f'{col2}:Q', title=titulo2)
        ]
    )
    
    return alt.layer(linea1, linea2).resolve_scale(
        y='independent'
    ).properties(
        height=400
    ).interactive()

def crear_heatmap_anual(df, columna, titulo):
    """Crea un heatmap anual para visualizar patrones temporales."""
    # Añadir columnas de mes y día
    df_heat = df.copy()
    df_heat['mes'] = df_heat.index.month
    df_heat['dia'] = df_heat.index.day
    df_heat['valor'] = df_heat[columna]
    df_heat = df_heat.reset_index()
    
    # Crear heatmap
    heatmap = alt.Chart(df_heat).mark_rect().encode(
        x=alt.X('mes:O', title='Mes', sort=list(range(1, 13))),
        y=alt.Y('dia:O', title='Día'),
        color=alt.Color('valor:Q', title=titulo, scale=alt.Scale(scheme='viridis')),
        tooltip=[
            alt.Tooltip('fecha:T', title='Fecha'),
            alt.Tooltip('valor:Q', title=titulo)
        ]
    ).properties(
        title=f"Heatmap de {titulo} por día",
        width=800,
        height=500
    )
    
    return heatmap

def app():
    """Función principal para la página de comparativas."""
    st.header("Comparativas")
    st.markdown("---")
    
    entradas = cargar_datos()
    df = preparar_dataframe_basico(entradas)
    
    # Tabs para diferentes tipos de comparativas
    tab1, tab2, tab3, tab4 = st.tabs(["Déficit vs Disponibilidad", "Análisis Temporal", "Correlaciones", "Plantas Termoeléctricas"])
    
    with tab1:
        st.subheader("Déficit vs Disponibilidad por Período")
        
        # Selección de rango de tiempo
        col1, col2 = st.columns([3, 1])
        with col1:
            # Selección de años
            anos = sorted(df.index.year.unique())
            sel_anos = st.multiselect("Seleccione años", [str(a) for a in anos], default=[str(anos[-1])])
        
        with col2:
            granularidad = st.radio("Granularidad", ["Diaria", "Mensual"])
        
        if sel_anos:
            # Filtrar datos por años seleccionados
            mask = df.index.year.isin([int(a) for a in sel_anos])
            df_filtered = df[mask]
            
            if not df_filtered.empty:
                # Resampling según granularidad
                if granularidad == "Mensual":
                    df_resampled = df_filtered.resample('M').mean()
                    fecha_format = '%b %Y'
                else:
                    df_resampled = df_filtered
                    fecha_format = '%d/%m/%Y'
                
                # Preparar datos para la visualización
                df_melted = pd.melt(
                    df_resampled.reset_index(), 
                    id_vars='fecha', 
                    value_vars=['deficit', 'disponibilidad'],
                    var_name='variable', 
                    value_name='valor'
                )
                
                # Formatear las fechas
                df_melted['fecha_str'] = df_melted['fecha'].dt.strftime(fecha_format)
                
                # Cambiar nombres para mejor visualización
                df_melted['variable'] = df_melted['variable'].map({
                    'deficit': 'Déficit', 
                    'disponibilidad': 'Disponibilidad'
                })
                
                # Crear gráfico interactivo
                chart = alt.Chart(df_melted).mark_line(point=True).encode(
                    x=alt.X('fecha:T', title='Fecha'),
                    y=alt.Y('valor:Q', title='MW'),
                    color=alt.Color('variable:N', legend=alt.Legend(title="Indicador")),
                    tooltip=[
                        alt.Tooltip('fecha_str:N', title='Fecha'),
                        alt.Tooltip('variable:N', title='Indicador'),
                        alt.Tooltip('valor:Q', title='Valor (MW)', format='.2f')
                    ]
                ).properties(
                    height=500
                ).interactive()
                
                st.altair_chart(chart, use_container_width=True)
                
                # Estadísticas
                st.subheader("Estadísticas Comparativas")
                
                # Tabla general
                deficit_mean = df_filtered['deficit'].mean()
                disp_mean = df_filtered['disponibilidad'].mean()
                demanda_mean = df_filtered['demanda'].mean()
                
                stats_general = {
                    "Métrica": ["Déficit Promedio (MW)", "Disponibilidad Promedio (MW)", "Demanda Promedio (MW)"],
                    "Valor": [
                        f"{deficit_mean:.2f}" if not pd.isna(deficit_mean) else "N/D",
                        f"{disp_mean:.2f}" if not pd.isna(disp_mean) else "N/D",
                        f"{demanda_mean:.2f}" if not pd.isna(demanda_mean) else "N/D"
                    ]
                }
                
                st.table(pd.DataFrame(stats_general))
                
                # Estadísticas por año
                stats_by_year = []
                for a in sel_anos:
                    year_data = df_filtered[df_filtered.index.year == int(a)]
                    stats_by_year.append({
                        "Año": a,
                        "Déficit Promedio (MW)": f"{year_data['deficit'].mean():.2f}" if not year_data['deficit'].isna().all() else "N/D",
                        "Disponibilidad Promedio (MW)": f"{year_data['disponibilidad'].mean():.2f}" if not year_data['disponibilidad'].isna().all() else "N/D",
                        "Días con Déficit": f"{(year_data['deficit'] > 0).sum()}" if not year_data['deficit'].isna().all() else "N/D",
                        "Máximo Déficit (MW)": f"{year_data['deficit'].max():.2f}" if not year_data['deficit'].isna().all() else "N/D"
                    })
                
                st.write("#### Estadísticas por Año")
                st.table(pd.DataFrame(stats_by_year))
            else:
                st.warning("No hay datos disponibles para los años seleccionados.")
        else:
            st.warning("Por favor, seleccione al menos un año para visualizar la comparativa.")
    
    with tab2:
        st.subheader("Análisis Temporal")
        
        # Selección del tipo de visualización
        tipo_vis = st.selectbox(
            "Tipo de Visualización", 
            ["Heatmap Anual", "Evolución Mensual", "Comparativa Interanual"]
        )
        
        # Selección de la métrica a visualizar
        metrica = st.selectbox(
            "Métrica a Visualizar", 
            ["deficit", "disponibilidad", "afectacion", "demanda"],
            format_func=lambda x: {
                "deficit": "Déficit",
                "disponibilidad": "Disponibilidad",
                "afectacion": "Afectación",
                "demanda": "Demanda"
            }[x]
        )
        
        # Título para los gráficos
        titulo_metrica = {
            "deficit": "Déficit (MW)",
            "disponibilidad": "Disponibilidad (MW)",
            "afectacion": "Afectación (MW)",
            "demanda": "Demanda (MW)"
        }[metrica]
        
        if tipo_vis == "Heatmap Anual":
            # Seleccionar año
            ano = st.selectbox("Seleccione Año", sorted(df.index.year.unique(), reverse=True))
            
            # Filtrar datos del año seleccionado
            df_year = df[df.index.year == ano]
            
            if not df_year.empty and not df_year[metrica].isna().all():
                # Crear heatmap usando la función auxiliar
                heatmap = crear_heatmap_anual(df_year, metrica, titulo_metrica)
                st.altair_chart(heatmap, use_container_width=True)
            else:
                st.info(f"No hay datos suficientes para el año {ano}")
        
        elif tipo_vis == "Evolución Mensual":
            # Agrupar datos por mes
            df_monthly = df.resample('M').mean()
            
            if not df_monthly.empty and not df_monthly[metrica].isna().all():
                # Crear dataframe para la visualización
                df_vis = df_monthly[[metrica]].copy().reset_index()
                df_vis['año'] = df_vis['fecha'].dt.year
                df_vis['mes'] = df_vis['fecha'].dt.month
                
                # Crear gráfico de líneas por año
                chart = alt.Chart(df_vis).mark_line(point=True).encode(
                    x=alt.X('mes:O', title='Mes', sort=list(range(1, 13))),
                    y=alt.Y(f'{metrica}:Q', title=titulo_metrica),
                    color=alt.Color('año:N', title='Año'),
                    tooltip=[
                        alt.Tooltip('año:N', title='Año'),
                        alt.Tooltip('mes:O', title='Mes'),
                        alt.Tooltip(f'{metrica}:Q', title=titulo_metrica)
                    ]
                ).properties(
                    title=f"Evolución mensual de {titulo_metrica}",
                    height=500
                ).interactive()
                
                st.altair_chart(chart, use_container_width=True)
            else:
                st.info("No hay datos suficientes para mostrar la evolución mensual")
        
        elif tipo_vis == "Comparativa Interanual":
            # Seleccionar años para comparar
            anos = sorted(df.index.year.unique())
            sel_anos = st.multiselect(
                "Seleccione años para comparar", 
                [str(a) for a in anos], 
                default=[str(anos[-1])] if anos else []
            )
            
            if sel_anos:
                # Crear dataframe para comparativa
                df_comp = pd.DataFrame()
                
                for a in sel_anos:
                    y = int(a)
                    year_data = df[df.index.year == y].copy()
                    year_data['dia_año'] = year_data.index.dayofyear
                    year_data['año'] = y
                    df_comp = pd.concat([df_comp, year_data])
                
                if not df_comp.empty and not df_comp[metrica].isna().all():
                    # Crear gráfico de líneas por día del año
                    chart = alt.Chart(df_comp.reset_index()).mark_line().encode(
                        x=alt.X('dia_año:Q', title='Día del año'),
                        y=alt.Y(f'{metrica}:Q', title=titulo_metrica),
                        color=alt.Color('año:N', title='Año'),
                        tooltip=[
                            alt.Tooltip('fecha:T', title='Fecha'),
                            alt.Tooltip(f'{metrica}:Q', title=titulo_metrica)
                        ]
                    ).properties(
                        title=f"Comparativa interanual de {titulo_metrica}",
                        height=500
                    ).interactive()
                    
                    st.altair_chart(chart, use_container_width=True)
                else:
                    st.info("No hay datos suficientes para los años seleccionados")
            else:
                st.warning("Por favor, seleccione al menos un año para la comparativa")
    
    with tab3:
        st.subheader("Análisis de Correlaciones")
        
        # Filtrar datos con suficientes columnas para análisis
        df_corr = df[['deficit', 'disponibilidad', 'demanda', 'afectacion']].copy()
        df_corr = df_corr.dropna()
        
        if not df_corr.empty:
            # Calcular matriz de correlación
            corr_matrix = df_corr.corr()
            
            # Mostrar matriz de correlación como tabla
            st.write("#### Matriz de Correlación")
            st.table(corr_matrix.style.format("{:.2f}"))
            
            # Selección de variables para diagrama de dispersión
            col1, col2 = st.columns(2)
            
            with col1:
                x_var = st.selectbox(
                    "Variable X", 
                    ["disponibilidad", "deficit", "demanda", "afectacion"],
                    format_func=lambda x: {
                        "deficit": "Déficit",
                        "disponibilidad": "Disponibilidad",
                        "afectacion": "Afectación",
                        "demanda": "Demanda"
                    }[x]
                )
            
            with col2:
                y_var = st.selectbox(
                    "Variable Y", 
                    ["deficit", "disponibilidad", "demanda", "afectacion"],
                    format_func=lambda x: {
                        "deficit": "Déficit",
                        "disponibilidad": "Disponibilidad",
                        "afectacion": "Afectación",
                        "demanda": "Demanda"
                    }[x],
                    index=1
                )
            
            # Crear diagrama de dispersión
            scatter = alt.Chart(df_corr.reset_index()).mark_circle(size=60).encode(
                x=alt.X(f'{x_var}:Q', title=f"{x_var.capitalize()} (MW)"),
                y=alt.Y(f'{y_var}:Q', title=f"{y_var.capitalize()} (MW)"),
                tooltip=[
                    alt.Tooltip('fecha:T', title='Fecha'),
                    alt.Tooltip(f'{x_var}:Q', title=f"{x_var.capitalize()} (MW)"),
                    alt.Tooltip(f'{y_var}:Q', title=f"{y_var.capitalize()} (MW)")
                ],
                color=alt.Color('fecha:T', legend=None)
            ).properties(
                height=500,
                title=f"Correlación entre {x_var.capitalize()} y {y_var.capitalize()}"
            ).interactive()
            
            # Añadir línea de regresión
            regression = scatter.transform_regression(x_var, y_var).mark_line(color='red')
            
            # Mostrar gráfico
            st.altair_chart(scatter + regression, use_container_width=True)
            
            # Calcular coeficiente de correlación
            corr_value = df_corr[x_var].corr(df_corr[y_var])
            st.write(f"**Coeficiente de correlación:** {corr_value:.4f}")
            
            # Interpretación del coeficiente
            if abs(corr_value) < 0.2:
                st.write("Interpretación: **Correlación muy baja o nula**")
            elif abs(corr_value) < 0.4:
                st.write("Interpretación: **Correlación baja**")
            elif abs(corr_value) < 0.6:
                st.write("Interpretación: **Correlación moderada**")
            elif abs(corr_value) < 0.8:
                st.write("Interpretación: **Correlación alta**")
            else:
                st.write("Interpretación: **Correlación muy alta**")
        else:
            st.warning("No hay suficientes datos para realizar análisis de correlaciones")

    with tab4:
        st.subheader("Análisis de Plantas Termoeléctricas")
        st.markdown("""
        Esta sección muestra el análisis de las centrales termoeléctricas del Sistema Eléctrico Nacional.
        Los nombres de las plantas han sido estandarizados para evitar duplicidades por variaciones en la nomenclatura.
        """)
        
        # Obtener plantas estandarizadas
        plantas = obtener_plantas(entradas)
        df_plantas = datos_estado_plantas(entradas)
        
        # No mostrar si no hay datos
        if df_plantas.empty:
            st.warning("No hay datos disponibles de plantas termoeléctricas")
            return
            
        # Selección de visualización
        visualizacion = st.radio(
            "Tipo de visualización",
            ["Frecuencia de estados", "Línea de tiempo", "Estadísticas por planta"]
        )
        
        if visualizacion == "Frecuencia de estados":
            # Selección de plantas
            plantas_seleccionadas = st.multiselect(
                "Seleccionar plantas para análisis",
                plantas,
                default=plantas[:5] if len(plantas) > 0 else []
            )
            
            if not plantas_seleccionadas:
                st.info("Seleccione al menos una planta para visualizar datos")
                return
                
            # Filtrar datos por plantas seleccionadas
            df_filtered = df_plantas[df_plantas['planta'].isin(plantas_seleccionadas)]
            
            # Contar frecuencia de estados por planta
            conteo = df_filtered.groupby(['planta', 'estado']).size().reset_index(name='frecuencia')
            
            # Crear gráfico de barras agrupadas
            chart = alt.Chart(conteo).mark_bar().encode(
                x=alt.X('planta:N', title='Planta', sort='-y'),
                y=alt.Y('frecuencia:Q', title='Días en este estado'),
                color=alt.Color('estado:N', title='Estado',
                               scale=alt.Scale(domain=['Avería', 'Mantenimiento'],
                                               range=['#e15759', '#4e79a7'])),
                tooltip=['planta:N', 'estado:N', 'frecuencia:Q']
            ).properties(
                title='Frecuencia de estados por planta',
                height=500
            ).interactive()
            
            st.altair_chart(chart, use_container_width=True)
            
            # Análisis adicional
            total_dias = len(df_filtered['fecha'].unique())
            st.write(f"**Período de análisis:** {total_dias} días")
            
            # Tabla de estadísticas
            stats = []
            for planta in plantas_seleccionadas:
                planta_df = df_filtered[df_filtered['planta'] == planta]
                dias_averia = len(planta_df[planta_df['estado'] == 'Avería'])
                dias_mant = len(planta_df[planta_df['estado'] == 'Mantenimiento'])
                total = dias_averia + dias_mant
                
                stats.append({
                    "Planta": planta,
                    "Días en avería": dias_averia,
                    "Días en mantenimiento": dias_mant,
                    "Total días con problemas": total,
                    "% del período analizado": f"{(total / total_dias * 100):.1f}%" if total_dias > 0 else "N/A"
                })
            
            st.write("#### Estadísticas por planta")
            st.table(pd.DataFrame(stats))
            
        elif visualizacion == "Línea de tiempo":
            # Selección de planta
            planta = st.selectbox("Seleccione una planta", plantas)
            
            if not planta:
                st.info("No hay plantas disponibles para análisis")
                return
                
            # Filtrar datos para la planta seleccionada
            df_planta = df_plantas[df_plantas['planta'] == planta]
            
            if df_planta.empty:
                st.info(f"No hay datos disponibles para la planta {planta}")
                return
                
            # Crear dataframe para visualización
            df_timeline = df_planta.copy()
            
            # Convertir a formato de línea de tiempo
            chart = alt.Chart(df_timeline).mark_point(size=100, filled=True).encode(
                x=alt.X('fecha:T', title='Fecha'),
                y=alt.Y('estado:N', title='Estado'),
                color=alt.Color('estado:N', 
                                scale=alt.Scale(domain=['Avería', 'Mantenimiento'],
                                               range=['#e15759', '#4e79a7'])),
                tooltip=['fecha:T', 'estado:N']
            ).properties(
                title=f'Línea de tiempo para {planta}',
                height=300
            ).interactive()
            
            st.altair_chart(chart, use_container_width=True)
            
            # Estadísticas adicionales
            fechas_unicas = df_timeline['fecha'].unique()
            primer_registro = min(fechas_unicas) if len(fechas_unicas) > 0 else None
            ultimo_registro = max(fechas_unicas) if len(fechas_unicas) > 0 else None
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Primer registro", primer_registro.strftime('%Y-%m-%d') if primer_registro else "N/A")
            with col2:
                st.metric("Último registro", ultimo_registro.strftime('%Y-%m-%d') if ultimo_registro else "N/A")
            
            # Calcular porcentajes de tiempo en cada estado
            total_registros = len(df_timeline)
            averia_count = len(df_timeline[df_timeline['estado'] == 'Avería'])
            mant_count = len(df_timeline[df_timeline['estado'] == 'Mantenimiento'])
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("% tiempo en avería", f"{averia_count/total_registros*100:.1f}%" if total_registros > 0 else "N/A")
            with col2:
                st.metric("% tiempo en mantenimiento", f"{mant_count/total_registros*100:.1f}%" if total_registros > 0 else "N/A")
            
        elif visualizacion == "Estadísticas por planta":
            # Calcular estadísticas para todas las plantas
            stats_all = []
            
            # Fechas únicas en todo el conjunto de datos
            all_dates = df_plantas['fecha'].unique()
            total_days = len(all_dates)
            
            for planta in plantas:
                df_planta = df_plantas[df_plantas['planta'] == planta]
                
                if df_planta.empty:
                    continue
                    
                dias_averia = len(df_planta[df_planta['estado'] == 'Avería'])
                dias_mant = len(df_planta[df_planta['estado'] == 'Mantenimiento'])
                total_problemas = dias_averia + dias_mant
                
                # Calcular el período más largo en cada estado
                periodos = []
                current_state = None
                current_start = None
                
                for date in sorted(all_dates):
                    # Buscar si hay registro para esta fecha
                    registros = df_planta[df_planta['fecha'] == date]
                    
                    if len(registros) > 0:
                        estado = registros.iloc[0]['estado']
                        
                        if current_state is None:
                            # Inicio de un nuevo período
                            current_state = estado
                            current_start = date
                        elif estado != current_state:
                            # Cambio de estado
                            periodos.append({
                                'estado': current_state,
                                'inicio': current_start,
                                'fin': date,
                                'duracion': (date - current_start).days
                            })
                            current_state = estado
                            current_start = date
                    else:
                        # No hay registro para esta fecha, terminar período actual si existe
                        if current_state is not None:
                            periodos.append({
                                'estado': current_state,
                                'inicio': current_start,
                                'fin': date,
                                'duracion': (date - current_start).days
                            })
                            current_state = None
                            current_start = None
                
                # Calcular períodos más largos
                if periodos:
                    periodo_averia = max([p['duracion'] for p in periodos if p['estado'] == 'Avería'], default=0)
                    periodo_mant = max([p['duracion'] for p in periodos if p['estado'] == 'Mantenimiento'], default=0)
                else:
                    periodo_averia = 0
                    periodo_mant = 0
                
                stats_all.append({
                    "Planta": planta,
                    "Días en avería": dias_averia,
                    "Días en mantenimiento": dias_mant,
                    "Total días con problemas": total_problemas,
                    "% del período analizado": f"{(total_problemas / total_days * 100):.1f}%" if total_days > 0 else "N/A",
                    "Período más largo en avería (días)": periodo_averia,
                    "Período más largo en mantenimiento (días)": periodo_mant
                })
            
            # Ordenar por total de días con problemas (descendente)
            stats_df = pd.DataFrame(stats_all).sort_values("Total días con problemas", ascending=False)
            
            # Mostrar tabla general
            st.write("#### Estadísticas generales por planta")
            st.write(f"Período de análisis: {total_days} días")
            st.dataframe(stats_df)
            
            # Visualización gráfica de las plantas con más problemas
            top_n = min(10, len(stats_df))
            top_plantas = stats_df.head(top_n)
            
            chart_data = pd.melt(
                top_plantas,
                id_vars=['Planta'],
                value_vars=['Días en avería', 'Días en mantenimiento'],
                var_name='Categoría',
                value_name='Días'
            )
            
            chart = alt.Chart(chart_data).mark_bar().encode(
                x=alt.X('Planta:N', sort='-y', title='Planta'),
                y=alt.Y('Días:Q', title='Días'),
                color=alt.Color('Categoría:N', 
                               scale=alt.Scale(domain=['Días en avería', 'Días en mantenimiento'],
                                              range=['#e15759', '#4e79a7'])),
                tooltip=['Planta:N', 'Categoría:N', 'Días:Q']
            ).properties(
                title=f'Top {top_n} plantas con más días de afectación',
                height=400
            ).interactive()
            
            st.altair_chart(chart, use_container_width=True)
