import streamlit as st
import json
import os
import pandas as pd
import altair as alt
import calendar
from datetime import datetime, date

import mapping

def DIAS_REPETIDOS(entradas):
    vistos = set()
    unicas = []
    for e in entradas:
        d = e["fecha"].date()
        if d not in vistos:
            vistos.add(d)
            unicas.append(e)
    return unicas

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
                entradas.append({"fecha": dt, "datos": rec["datos"]})
    return DIAS_REPETIDOS(entradas)

def preparar_dataframe(entradas):
    filas = []
    for e in entradas:
        pred = e["datos"].get("prediccion", {})
        filas.append({
            "fecha": e["fecha"],
            "afectacion": pred.get("afectacion"),
            "demanda": pred.get("demanda_maxima")
        })
    return pd.DataFrame(filas).set_index("fecha").sort_index()

def mostrar_reciente(entradas, df):
    st.subheader("Datos del Ultimo Dia")
    if df.empty:
        st.error("No hay datos.")
        return
    fm = df.index.date.max()
    recs = [e for e in entradas if e["fecha"].date() == fm]
    if not recs:
        st.error("No se reportaron datos.")
        return
    for e in recs:
        d = e["datos"]
        st.write("Fecha: " + e["fecha"].strftime("%d/%m/%Y"))
        st.write("Afectacion: " + str(d.get("prediccion",{}).get("afectacion","No disponible")) + " MW")
        st.write("Demanda maxima: " + str(d.get("prediccion",{}).get("demanda_maxima","No disponible")) + " MW")
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

def mostrar_vista_global(entradas, df):
    st.subheader("Vista Global")
    anos = sorted(df.index.year.unique())
    opcion = st.selectbox("Seleccione año o Todos los Anos", ["Todos los Anos"] + [str(y) for y in anos])
    if opcion == "Todos los Anos":
        serie = df["afectacion"].resample("D").sum()
        st.line_chart(serie)
    else:
        y = int(opcion)
        df_y = df[df.index.year == y]
        meses = sorted(df_y.index.month.unique())
        nombres = [calendar.month_name[m] for m in meses]
        opcion_mes = st.selectbox("Seleccione mes o Año completo", ["Año completo"] + nombres)
        if opcion_mes == "Año completo":
            st.line_chart(df_y["afectacion"].resample("D").sum())
        else:
            m = nombres.index(opcion_mes) + 1
            df_m = df_y[df_y.index.month == m]
            st.line_chart(df_m["afectacion"].resample("D").sum())
            dias = sorted({d.date().isoformat() for d in df_m.index})
            opcion_dia = st.selectbox("Seleccione día o Total del Mes", ["Total del Mes"] + dias)
            if opcion_dia != "Total del Mes":
                sel = datetime.fromisoformat(opcion_dia).date()
                recs = [e for e in entradas if e["fecha"].date() == sel]
                for e in recs:
                    d = e["datos"]
                    st.write("Fecha: " + e["fecha"].strftime("%d/%m/%Y"))
                    st.write("Afectacion: " + str(d.get("prediccion",{}).get("afectacion","No disponible")) + " MW")
                    st.write("Demanda maxima: " + str(d.get("prediccion",{}).get("demanda_maxima","No disponible")) + " MW")
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

def mostrar_comparativa(entradas, df):
    st.subheader("Comparativa multi-anio")
    anos = sorted(df.index.year.unique())
    sel_anos = st.multiselect("Seleccione anos", [str(a) for a in anos], default=[str(anos[-1])])
    inicio, fin = st.slider(
        "Rango (mes-dia)",
        min_value=date(2000,1,1),
        max_value=date(2000,12,31),
        value=(date(2000,1,1), date(2000,12,31)),
        format="MM-DD"
    )
    mostrar_media = st.checkbox("Mostrar media de cada ano")
    filas = []
    for a in sel_anos:
        y = int(a)
        sd = date(y, inicio.month, inicio.day)
        ed = date(y, fin.month, fin.day)
        sub = df[(df.index.date>=sd)&(df.index.date<=ed)&(df.index.year==y)]
        for idx, row in sub.iterrows():
            filas.append({"fecha": idx, "anio": a, "afectacion": row["afectacion"], "demanda": row["demanda"]})
    if not filas:
        st.error("No hay datos para los anos y rango seleccionados.")
        return
    df_comp = pd.DataFrame(filas)
    chart1 = (
        alt.Chart(df_comp)
        .mark_line()
        .encode(x="fecha:T", y="afectacion:Q", color="anio:N", tooltip=["anio:N","fecha:T","afectacion:Q"])
        .interactive()
    )
    st.altair_chart(chart1, use_container_width=True)
    fold = df_comp.melt(id_vars=["fecha","anio"], value_vars=["afectacion","demanda"],
                        var_name="metric", value_name="valor")
    chart2 = (
        alt.Chart(fold)
        .mark_line()
        .encode(
            x="fecha:T", y="valor:Q",
            color="metric:N", strokeDash="anio:N",
            tooltip=["anio:N","metric:N","fecha:T","valor:Q"]
        )
        .interactive()
    )
    st.altair_chart(chart2, use_container_width=True)
    st.write("### Dias con averia por planta")
    plantas = []
    for e in entradas:
        pls = e["datos"].get("plantas", {})
        for clave in ("averia","mantenimiento"):
            for p in pls.get(clave, []):
                n = p.get("planta")
                if n and n not in plantas:
                    plantas.append(n)
    cont = {p:0 for p in plantas}
    for e in entradas:
        d = e["fecha"].date()
        if any(date(int(a), inicio.month, inicio.day) <= d <= date(int(a), fin.month, fin.day) for a in sel_anos):
            aver = set(p["planta"] for p in e["datos"].get("plantas",{}).get("averia",[]) if p.get("planta"))
            for p in aver:
                cont[p]+=1
    df_pl = pd.DataFrame([{"planta":p,"dias_averia":cont[p]} for p in plantas])
    st.table(df_pl.sort_values("dias_averia", ascending=False))

def app():
    entradas = cargar_datos()
    df = preparar_dataframe(entradas)
    with st.expander("Deficit: Datos del Ultimo Dia", expanded=True):
        mostrar_reciente(entradas, df)
    with st.expander("Deficit: Vista Global", expanded=False):
        mostrar_vista_global(entradas, df)
    with st.expander("Deficit: Comparativa", expanded=False):
        mostrar_comparativa(entradas, df)
