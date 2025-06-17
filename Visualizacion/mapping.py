def format_prediccion(pred):
    lines = []
    lines.append(
        f"Afectación total: {pred.get('afectacion')} MW"
        if pred.get('afectacion') is not None
        else "Afectación total: No se reportaron datos"
    )
    lines.append(
        f"Disponibilidad: {pred.get('disponibilidad')} MW"
        if pred.get('disponibilidad') is not None
        else "Disponibilidad: No se reportaron datos"
    )
    lines.append(
        f"Demanda máxima: {pred.get('demanda_maxima')} MW"
        if pred.get('demanda_maxima') is not None
        else "Demanda máxima: No se reportaron datos"
    )
    lines.append(
        f"Déficit: {pred.get('deficit')} MW"
        if pred.get('deficit') is not None
        else "Déficit: No se reportaron datos"
    )
    lines.append(
        f"Respaldo: {pred.get('respaldo')} MW"
        if pred.get('respaldo') is not None
        else "Respaldo: No se reportaron datos"
    )
    lines.append(
        f"Horario pico: {pred.get('horario_pico')}"
        if pred.get('horario_pico')
        else "Horario pico: No se reportaron datos"
    )
    return lines

def format_info_matutina(info):
    lines = []
    lines.append(f"Informe matutino ({info.get('hora')}):")
    lines.append(
        f"- Disponibilidad: {info.get('disponibilidad')} MW"
        if info.get('disponibilidad') is not None
        else "- Disponibilidad: No se reportaron datos"
    )
    lines.append(
        f"- Demanda: {info.get('demanda')} MW"
        if info.get('demanda') is not None
        else "- Demanda: No se reportaron datos"
    )
    lines.append(
        f"- Déficit: {info.get('deficit')} MW"
        if info.get('deficit') is not None
        else "- Déficit: No se reportaron datos"
    )
    proj = info.get('proyeccion_mediodia', {})
    if proj:
        lines.append(
            f"- Proyección mediodía: {proj.get('afectacion_estimada')} MW a las {proj.get('hora_estimada')}"
            if proj.get('afectacion_estimada') is not None
            else "- Proyección mediodía: No se reportaron datos"
        )
    else:
        lines.append("- Proyección mediodía: No se reportaron datos")
    return lines

from .plant_standardizer import get_canonical_plant_name

def format_plantas(plantas):
    lines = []
    averias = plantas.get('averia', [])
    mant = plantas.get('mantenimiento', [])
    term = plantas.get('limitacion_termica', {})
    if averias:
        # Apply name standardization
        names = [get_canonical_plant_name(p.get('planta')) for p in averias if p.get('planta')]
        # Filter out None values and remove duplicates but preserve order
        unique_names = []
        for name in names:
            if name and name not in unique_names:
                unique_names.append(name)
        lines.append(f"Plantas con avería: {', '.join(unique_names)}" if unique_names else "Plantas con avería: No se reportaron datos")
    else:
        lines.append("Plantas con avería: No se reportaron datos")
    if mant:
        # Apply name standardization
        names = [get_canonical_plant_name(p.get('planta')) for p in mant if p.get('planta')]
        # Filter out None values and remove duplicates but preserve order
        unique_names = []
        for name in names:
            if name and name not in unique_names:
                unique_names.append(name)
        lines.append(f"Plantas en mantenimiento: {', '.join(unique_names)}" if unique_names else "Plantas en mantenimiento: No se reportaron datos")
    else:
        lines.append("Plantas en mantenimiento: No se reportaron datos")
    if term.get('mw_afectados') is not None:
        lines.append(f"Limitación térmica: {term.get('mw_afectados')} MW")
    else:
        lines.append("Limitación térmica: No se reportaron datos")
    return lines

def format_distribuida(dist):
    lines = []
    motores = dist.get('motores_con_problemas', {})
    if motores.get('total') is not None:
        lines.append(f"Motores con problemas: {motores.get('total')} unidades ({motores.get('impacto_mw')} MW)")
    else:
        lines.append("Motores con problemas: No se reportaron datos")
    lub = dist.get('problemas_lubricantes', {})
    if lub.get('mw_afectados') is not None:
        lines.append(f"Problemas de lubricantes: {lub.get('mw_afectados')} MW")
    else:
        lines.append("Problemas de lubricantes: No se reportaron datos")
    patanas = dist.get('patanas_con_problemas', [])
    if patanas:
        lines.append("Patana(s) con problemas:")
        for p in patanas:
            nombre = p.get('patana_nombre') or "Nombre no disponible"
            m_aff = p.get('motores_afectados')
            mw_aff = p.get('mw_afectados')
            rec = p.get('recuperacion_estimada', {})
            rec_m = rec.get('motores')
            rec_mw = rec.get('mw')
            rec_h = rec.get('horario') or "Hora no disponible"
            rec_e = rec.get('estado') or "Estado no disponible"
            lines.append(f"  • {nombre}")
            lines.append(f"    - Motores afectados: {m_aff if m_aff is not None else 'No se reportaron datos'}")
            lines.append(f"    - MW afectados: {mw_aff if mw_aff is not None else 'No se reportaron datos'}")
            lines.append(f"    - Recuperación estimada: {rec_m if rec_m is not None else 'N/D'} motores, {rec_mw if rec_mw is not None else 'N/D'} MW")
            lines.append(f"    - Horario estimado: {rec_h}")
            lines.append(f"    - Estado: {rec_e}")
    else:
        lines.append("Patana(s) con problemas: No se reportaron datos")
    return lines

def format_paneles_solares(paneles):
    lines = []
    if paneles.get('cantidad_parques') is not None:
        lines.append(f"Cantidad de parques solares: {paneles.get('cantidad_parques')}")
    else:
        lines.append("Cantidad de parques solares: No se reportaron datos")
    if paneles.get('produccion_mwh') is not None:
        lines.append(f"Producción solar: {paneles.get('produccion_mwh')} MWh")
    else:
        lines.append("Producción solar: No se reportaron datos")
    if paneles.get('nuevos_parques') is not None:
        lines.append(f"Nuevos parques: {paneles.get('nuevos_parques')}")
    else:
        lines.append("Nuevos parques: No se reportaron datos")
    if paneles.get('capacidad_instalada') is not None:
        lines.append(f"Capacidad instalada: {paneles.get('capacidad_instalada')}")
    else:
        lines.append("Capacidad instalada: No se reportaron datos")
    if paneles.get('periodo_produccion'):
        lines.append(f"Periodo de producción: {paneles.get('periodo_produccion')}")
    else:
        lines.append("Periodo de producción: No se reportaron datos")
    return lines

def format_impacto(impacto):
    lines = []
    if impacto.get('horas_totales') is not None:
        lines.append(f"Horas totales de afectación: {impacto.get('horas_totales')}")
    else:
        lines.append("Horas totales de afectación: No se reportaron datos")
    if impacto.get('continuidad_afectacion'):
        lines.append(f"Continuidad de afectación: {impacto.get('continuidad_afectacion')}")
    else:
        lines.append("Continuidad de afectación: No se reportaron datos")
    maximo = impacto.get('maximo', {})
    if maximo.get('mw') is not None:
        lines.append(f"Impacto máximo: {maximo.get('mw')} MW a las {maximo.get('hora')} ({maximo.get('fecha')})")
    else:
        lines.append("Impacto máximo: No se reportaron datos")
    if impacto.get('tendencia'):
        lines.append(f"Tendencia: {impacto.get('tendencia')}")
    else:
        lines.append("Tendencia: No se reportaron datos")
    return lines
