import streamlit as st
import json
import os
import pandas as pd
import altair as alt
from datetime import datetime, date

import mapping

# elimina dias repetidos dejando solo la primera entrada de cada dia
def DIAS_REPETIDOS(entradas):
    vistos = set()
    unicas = []
    for e in entradas:
        dia = e["fecha"].date()
        if dia not in vistos:
            vistos.add(dia)
            unicas.append(e)
    return unicas

st.set_page_config(layout="wide")

base_dir = os.path.dirname(__file__)
ruta_json = os.path.join(base_dir, os.pardir, "data", "processed", "datos_electricos_organizados.json")
with open(ruta_json, "r", encoding="utf-8") as f:
    datos_crudos = json.load(f)

entradas = []
for anio in datos_crudos:
    for mes in datos_crudos[anio]:
        for reg in datos_crudos[anio][mes]:
            fecha = datetime.fromisoformat(reg["fecha"])
            entradas.append({"fecha": fecha, "datos": reg["datos"]})
entradas = DIAS_REPETIDOS(entradas)

datos_grafico = []
for e in entradas:
    pred = e["datos"].get("prediccion", {})
    afect = pred.get("afectacion") if isinstance(pred, dict) else None
    datos_grafico.append({"fecha": e["fecha"], "afectacion": afect})
df_grafico = pd.DataFrame(datos_grafico).set_index("fecha").sort_index()

st.title("Deficit")

with st.expander("Afectacion del dia mas reciente", expanded=True):
    fecha_reciente = df_grafico.index.date.max() if not df_grafico.empty else None
    entradas_recientes = [e for e in entradas if e["fecha"].date() == fecha_reciente] if fecha_reciente else []
    if not entradas_recientes:
        st.error("No se reportaron datos.")
    else:
        for e in entradas_recientes:
            d = e["datos"]
            st.write("Fecha: " + e["fecha"].strftime("%d/%m/%Y"))
            zonas = d.get("zonas_con_problemas") or []
            if zonas:
                texto = zonas[0]
                for z in zonas[1:]:
                    texto += ", " + z
                st.write("Zonas con problemas: " + texto)
            else:
                st.write("Zonas con problemas: No se reportaron datos")
            rep = d.get("fecha_reporte")
            st.write("Fecha de reporte: " + (rep or "No se reportaron datos"))
            st.write("---")
            for fn in [
                mapping.format_prediccion,
                mapping.format_info_matutina,
                mapping.format_plantas,
                mapping.format_distribuida,
                mapping.format_paneles_solares,
                mapping.format_impacto
            ]:
                clave = fn.__name__.split("_",1)[1]
                sec = d.get(clave, {})
                for linea in fn(sec):
                    st.write(linea)

with st.expander("Afectacion Historica", expanded=False):
    opciones_anio = ["Afectacion Total"] + [str(a) for a in sorted(df_grafico.index.year.unique())]
    opcion_anio = st.selectbox("Seleccione anio o Afectacion Total", opciones_anio)
    if opcion_anio == "Afectacion Total":
        df_diario = df_grafico.resample("D").sum()
        st.line_chart(df_diario["afectacion"])
    else:
        df_anio = df_grafico[df_grafico.index.year == int(opcion_anio)]
        opciones_mes = ["Afectacion Total"] + [str(m) for m in sorted(df_anio.index.month.unique())]
        opcion_mes = st.selectbox("Seleccione mes o Afectacion Total", opciones_mes)
        if opcion_mes == "Afectacion Total":
            st.line_chart(df_anio.resample("D").sum()["afectacion"])
        else:
            df_mes = df_anio[df_anio.index.month == int(opcion_mes)]
            dias = sorted({d.date().isoformat() for d in df_mes.index})
            opcion_dia = st.selectbox("Seleccione dia o Afectacion Total", ["Afectacion Total"] + dias)
            if opcion_dia == "Afectacion Total":
                st.line_chart(df_mes.resample("D").sum()["afectacion"])
            else:
                sel = datetime.fromisoformat(opcion_dia).date()
                entr_dia = [e for e in entradas if e["fecha"].date() == sel]
                if not entr_dia:
                    st.error("No se reportaron datos.")
                else:
                    for e in entr_dia:
                        d = e["datos"]
                        st.write("Fecha: " + e["fecha"].strftime("%d/%m/%Y"))
                        zonas = d.get("zonas_con_problemas") or []
                        if zonas:
                            texto = zonas[0]
                            for z in zonas[1:]:
                                texto += ", " + z
                            st.write("Zonas con problemas: " + texto)
                        else:
                            st.write("Zonas con problemas: No se reportaron datos")
                        st.write("Fecha de reporte: " + (d.get("fecha_reporte") or "No se reportaron datos"))
                        st.write("---")
                        for fn in [
                            mapping.format_prediccion,
                            mapping.format_info_matutina,
                            mapping.format_plantas,
                            mapping.format_distribuida,
                            mapping.format_paneles_solares,
                            mapping.format_impacto
                        ]:
                            clave = fn.__name__.split("_",1)[1]
                            for linea in fn(d.get(clave, {})):
                                st.write(linea)

with st.expander("Comparativas", expanded=False):
    seleccion_anios = st.multiselect(
        "Seleccione anos",
        [str(a) for a in sorted(df_grafico.index.year.unique())],
        default=[str(df_grafico.index.year.max())]
    )
    rango = st.slider(
        "Seleccione rango de fechas (mes-día)",
        value=(date(2000,1,1), date(2000,12,31)),
        min_value=date(2000,1,1),
        max_value=date(2000,12,31),
        format="MM-DD"
    )
    mostrar_media = st.checkbox("Mostrar linea de media")
    dfs = []
    for a in seleccion_anios:
        year = int(a)
        start = rango[0]
        end = rango[1]
        start_dt = date(year, start.month, start.day)
        end_dt = date(year, end.month, end.day)
        df_temp = df_grafico[(df_grafico.index.date >= start_dt) & (df_grafico.index.date <= end_dt) & (df_grafico.index.year == year)]
        if not df_temp.empty:
            df_temp2 = df_temp.reset_index()
            df_temp2["anio"] = str(year)
            dfs.append(df_temp2)
    if dfs:
        df_comp = pd.concat(dfs)
        chart = alt.Chart(df_comp).mark_line().encode(
            x="fecha:T",
            y="afectacion:Q",
            color="anio:N"
        )
        if mostrar_media:
            media_global = df_comp["afectacion"].mean()
            df_rule = pd.DataFrame({"y":[media_global]})
            rule = alt.Chart(df_rule).mark_rule().encode(y="y:Q")
            chart = chart + rule
        st.altair_chart(chart, use_container_width=True)
    else:
        st.error("No hay datos para los anios y rango seleccionados.")
