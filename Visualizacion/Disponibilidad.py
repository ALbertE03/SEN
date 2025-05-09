import streamlit as st
import json
import os
import pandas as pd
import altair as alt
from datetime import datetime, date

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
            "disponibilidad": pred.get("disponibilidad"),
            "demanda": pred.get("demanda_maxima")
        })
    return pd.DataFrame(filas).set_index("fecha").sort_index()

def preparar_datos_solares(entradas):
    filas_gen = []
    filas_cnt = []
    for e in entradas:
        d = e["fecha"]
        sol = e["datos"].get("paneles_solares", {})
        filas_gen.append({"fecha": d, "produccion_mwh": sol.get("produccion_mwh")})
        filas_cnt.append({"fecha": d, "parques": sol.get("cantidad_parques")})
    df_gen = pd.DataFrame(filas_gen).set_index("fecha").sort_index()
    df_cnt = pd.DataFrame(filas_cnt).set_index("fecha").sort_index()
    return df_gen, df_cnt

def obtener_plantas(entradas):
    plantas = set()
    for e in entradas:
        pls = e["datos"].get("plantas", {})
        for clave in ("averia","mantenimiento"):
            for p in pls.get(clave, []):
                nombre = p.get("planta")
                if nombre:
                    plantas.add(nombre)
    return sorted(plantas)

def contar_dias_operativos(entradas, plantas, sel_anos, inicio, fin):
    cont = {p:0 for p in plantas}
    for e in entradas:
        d = e["fecha"].date()
        for a in sel_anos:
            y = int(a)
            start_dt = date(y, inicio.month, inicio.day)
            end_dt   = date(y, fin.month,    fin.day)
            if start_dt <= d <= end_dt:
                pls = e["datos"].get("plantas",{})
                aver = set(p["planta"] for p in pls.get("averia",[]) if p.get("planta"))
                mant = set(p["planta"] for p in pls.get("mantenimiento",[]) if p.get("planta"))
                for p in plantas:
                    if p not in aver and p not in mant:
                        cont[p] += 1
    return cont

def app():
    entradas = cargar_datos()
    df = preparar_dataframe(entradas)
    df_solar_gen, df_solar_cnt = preparar_datos_solares(entradas)
    plantas = obtener_plantas(entradas)

    with st.expander("Disponibilidad: Comparativa y Analisis", expanded=True):
        anos = sorted(df.index.year.unique())
        sel_anos = st.multiselect("Seleccione anos", [str(a) for a in anos], default=[str(anos[-1])])
        inicio, fin = st.slider(
            "Rango (mes-dia)",
            min_value=date(2000,1,1),
            max_value=date(2000,12,31),
            value=(date(2000,1,1), date(2000,12,31)),
            format="MM-DD"
        )
        mostrar_media = st.checkbox("Mostrar media")

        # armar comparativa de disponibilidad y demanda
        filas = []
        for a in sel_anos:
            y = int(a)
            sd = date(y, inicio.month, inicio.day)
            ed = date(y, fin.month,    fin.day)
            sub = df[(df.index.date>=sd)&(df.index.date<=ed)&(df.index.year==y)]
            for idx, row in sub.iterrows():
                filas.append({"fecha": idx, "anio": a, "disponibilidad": row["disponibilidad"], "demanda": row["demanda"]})
        if filas:
            df_comp = pd.DataFrame(filas)

            # disponibilidad por año
            chart1 = (
                alt.Chart(df_comp)
                .mark_line()
                .encode(
                    x="fecha:T",
                    y="disponibilidad:Q",
                    color="anio:N",
                    tooltip=["anio:N","fecha:T","disponibilidad:Q"]
                )
                .interactive()
            )
            if mostrar_media:
                medios = [{"anio": a, "y": df_comp[df_comp["anio"]==a]["disponibilidad"].mean()} for a in sel_anos]
                df_med = pd.DataFrame(medios)
                rule = alt.Chart(df_med).mark_rule().encode(y="y:Q", color="anio:N")
                chart1 = chart1 + rule
            st.altair_chart(chart1, use_container_width=True)

            # disponibilidad vs demanda
            fold = df_comp.melt(
                id_vars=["fecha","anio"],
                value_vars=["disponibilidad","demanda"],
                var_name="metric", value_name="valor"
            )
            chart2 = (
                alt.Chart(fold)
                .mark_line()
                .encode(
                    x="fecha:T",
                    y="valor:Q",
                    color="metric:N",
                    strokeDash="anio:N",
                    tooltip=["anio:N","metric:N","fecha:T","valor:Q"]
                )
                .interactive()
            )
            if mostrar_media:
                medios2 = [{"metric": m, "y": df_comp[m].mean()} for m in ["disponibilidad","demanda"]]
                df_med2 = pd.DataFrame(medios2)
                rule2 = alt.Chart(df_med2).mark_rule().encode(y="y:Q", color="metric:N")
                chart2 = chart2 + rule2
            st.altair_chart(chart2, use_container_width=True)
        else:
            st.error("No hay datos para los anos y rango seleccionados.")

        st.write("### Parques solares en el periodo")
        solar_cnt = df_solar_cnt.reset_index()
        solar_cnt["mesdia"] = solar_cnt["fecha"].dt.strftime("%m-%d")
        solar_cnt = solar_cnt[
            (solar_cnt["mesdia"]>=inicio.strftime("%m-%d")) &
            (solar_cnt["mesdia"]<=fin.strftime("%m-%d")) &
            (solar_cnt["fecha"].dt.year.astype(str).isin(sel_anos))
        ]
        bar = (
            alt.Chart(solar_cnt)
            .mark_bar()
            .encode(x="fecha:T", y="parques:Q", tooltip=["fecha:T","parques:Q"])
        )
        st.altair_chart(bar, use_container_width=True)

        st.write("### Produccion solar (MWh) en el periodo")
        gen = df_solar_gen.reset_index()
        gen["mesdia"] = gen["fecha"].dt.strftime("%m-%d")
        gen = gen[
            (gen["mesdia"]>=inicio.strftime("%m-%d")) &
            (gen["mesdia"]<=fin.strftime("%m-%d")) &
            (gen["fecha"].dt.year.astype(str).isin(sel_anos))
        ]
        line_solar = (
            alt.Chart(gen)
            .mark_line()
            .encode(x="fecha:T", y="produccion_mwh:Q", tooltip=["fecha:T","produccion_mwh:Q"])
            .interactive()
        )
        st.altair_chart(line_solar, use_container_width=True)

        st.write("### Dias operativos por planta")
        cont = contar_dias_operativos(entradas, plantas, sel_anos, inicio, fin)
        df_pl = pd.DataFrame([{"planta":p,"dias_operativos":cont[p]} for p in plantas])
        st.table(df_pl.sort_values("dias_operativos", ascending=False))
