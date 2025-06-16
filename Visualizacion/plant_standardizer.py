"""
Módulo para la estandarización de nombres de plantas termoeléctricas del Sistema Eléctrico Nacional.

Este módulo contiene el mapeo manual y las funciones de normalización para asegurar
que los diferentes nombres utilizados para la misma planta termoeléctrica
sean estandarizados a un nombre canónico único.
"""

# Grupos de plantas termoeléctricas principales con sus variaciones de nombres
# Cada grupo corresponde a una planta real
# Estos nombres se han agrupado manualmente tras analizar todos los datos

# Lista completa y normalizada de plantas termoeléctricas
PLANTAS_CANONICAS = [
    "Antonio Guiteras",      # Matanzas
    "Felton",                # Holguín (también conocida como Lidio Ramón Pérez)
    "Renté",                 # Santiago de Cuba (también conocida como Antonio Maceo)
    "Santa Cruz",            # Mayabeque (también conocida como Ernesto Guevara o Ernesto Che Guevara)
    "Cienfuegos",            # Cienfuegos (también conocida como Carlos Manuel de Céspedes)
    "Mariel",                # Artemisa (también conocida como Máximo Gómez)
    "Nuevitas",              # Camagüey (también conocida como 10 de Octubre o Diez de Octubre)
    "Tallapiedra",           # La Habana
    "Otto Parellada",        # La Habana
    "Habana",                # La Habana (CTE Habana)
    
    # Otras plantas o centrales de generación
    "Energas Boca de Jaruco", # Generación con gas
    "Energas Jaruco",        # Generación con gas
    "Energas Varadero",      # Generación con gas
    "Boca de Jaruco",        # Mayabeque
    "CTE Matanzas",          # Matanzas
]

# Mapeo de todas las variantes de nombres a su forma canónica
PLANT_NAME_MAPPING = {
    # Antonio Guiteras (Matanzas)
    "Antonio Guiteras": "Antonio Guiteras",
    "CTE Antonio Guiteras": "Antonio Guiteras",
    "CTE Guiteras": "Antonio Guiteras",
    "Guiteras": "Antonio Guiteras",
    "Central Termoeléctrica Antonio Guiteras": "Antonio Guiteras",
    "termoeléctrica Antonio Guiteras": "Antonio Guiteras",
    "Central Termoeléctrica (CTE) Antonio Guiteras": "Antonio Guiteras",
    
    # Felton (Lidio Ramón Pérez, Holguín)
    "Felton": "Felton",
    "CTE Felton": "Felton",
    "CTE de Felton": "Felton",
    "CTE Felto": "Felton",
    "Lidio Ramón Pérez": "Felton",
    "CTE Lidio Ramón Pérez": "Felton",
    "CTE Lidio Ramón Pérez (Felton)": "Felton",
    "Central Termoeléctrica (CTE) Felton": "Felton",
    "Central Termoeléctrica Felton 1": "Felton",
    "Feltón 2": "Felton",
    "CTE ETE Lidio Ramón Pérez Felton": "Felton",
    "Lidio Ramón Pérez (Holguín)": "Felton",
    
    # Renté (Antonio Maceo, Santiago de Cuba)
    "Renté": "Renté",
    "Rente": "Renté",
    "CTE Renté": "Renté",
    "CTE Rente": "Renté",
    "termoeléctrica Renté": "Renté", 
    "Antonio Maceo": "Renté",
    "CTE Antonio Maceo": "Renté",
    "CTE Antonio Maceo (Rente)": "Renté",
    "CTE Antonio Maceo ( Rente)": "Renté",
    "CTE René": "Renté",
    
    # Santa Cruz (Ernesto Guevara, Mayabeque)
    "Santa Cruz": "Santa Cruz",
    "CTE Santa Cruz": "Santa Cruz",
    "Ernesto Guevara": "Santa Cruz",
    "CTE Ernesto Guevara": "Santa Cruz",
    "CTE Ernesto Guevara (Santa Cruz)": "Santa Cruz",
    "CTE Ernesto Che Guevara": "Santa Cruz",
    
    # Cienfuegos (Carlos Manuel de Céspedes)
    "Cienfuegos": "Cienfuegos",
    "CTE Cienfuegos": "Cienfuegos",
    "CTE de Cienfuegos": "Cienfuegos",
    "termoeléctrica Cienfuegos": "Cienfuegos",
    "Carlos Manuel de Céspedes": "Cienfuegos",
    "termoeléctrica Carlos Manuel de Céspedes": "Cienfuegos",
    "CTE Carlos Manuel de Céspedes": "Cienfuegos",
    "CTE Carlos Manuel de Cespedes": "Cienfuegos",
    "CTE Carlos M. de Céspedes": "Cienfuegos",
    "CTE Céspedes": "Cienfuegos",
    "Céspedes": "Cienfuegos",
    "Central Termoeléctrica de Cienfuegos Carlos Manuel de Céspedes": "Cienfuegos",
    "CTE Empresa Eléctrica Cienfuegos": "Cienfuegos",
    
    # Mariel (Máximo Gómez, Artemisa)
    "Mariel": "Mariel",
    "CTE Mariel": "Mariel",
    "termoeléctrica Mariel": "Mariel",
    "Máximo Gómez": "Mariel",
    "CTE Máximo Gómez": "Mariel",
    "CTE Máximo Gómez (Mariel)": "Mariel",
    "Máximo Gómez (Mariel)": "Mariel",
    "Mariel 8": "Mariel",
    "termoeléctrica del Mariel": "Mariel",
    
    # Nuevitas (10 de Octubre, Camagüey)
    "Nuevitas": "Nuevitas",
    "CTE Nuevitas": "Nuevitas",
    "Nuevitas (Camagüey)": "Nuevitas",
    "Diez de Octubre": "Nuevitas",
    "CTE Diez de Octubre": "Nuevitas", 
    "CTE Diez de Octubre ( Nuevitas)": "Nuevitas",
    "CTE 10 de Octubre": "Nuevitas",
    
    # Tallapiedra (La Habana)
    "Tallapiedra": "Tallapiedra",
    "CTE Tallapiedra": "Tallapiedra",
    "Talla Piedra": "Tallapiedra",
    "CTE Talla Piedra": "Tallapiedra",
    "Talla piedra": "Tallapiedra",
    
    # Otto Parellada (La Habana)
    "Otto Parellada": "Otto Parellada",
    "CTE Otto Parellada": "Otto Parellada",
    
    # Otras plantas termoeléctricas
    "CTE Habana": "Habana",
    "Habana": "Habana",
    "CTE Matanzas": "CTE Matanzas",
      # Otras plantas o centrales
    "Energas Boca de Jaruco": "Energas Boca de Jaruco",
    "Energás Boca de Jaruco": "Energas Boca de Jaruco",
    "Boca de Jaruco": "Boca de Jaruco",
    "Energas Jaruco": "Energas Jaruco",
    "Energas Varadero": "Energas Varadero",
    "Energas": "Energas Boca de Jaruco",  # Asumimos que Energas genérico se refiere a Boca de Jaruco
    "CTE Matanzas": "CTE Matanzas",  # Mantener como está ya que no encaja en las principales
    
    # Entradas problemáticas - Ignorar o tratar especialmente
    "CTE Para": None,  # No es una central real, parece ser un error
    "CTE": None,  # Demasiado genérico para ser útil
    
    # Agrupaciones que no son plantas individuales
    "CTE Santa Cruz, Cienfuegos y Renté": None,
    "Santa Cruz, Cienfuegos y Renté": None,
}

def get_canonical_plant_name(plant_name):
    """
    Convierte cualquier variante de nombre de planta termoeléctrica a su forma canónica.
    
    Args:
        plant_name (str): Nombre original de la planta termoeléctrica
        
    Returns:
        str: Nombre canónico de la planta, o el original si no hay mapeo
    """
    if not plant_name:
        return plant_name
    
    # Buscar el nombre canónico en el mapeo
    return PLANT_NAME_MAPPING.get(plant_name, plant_name)

def get_valid_plant_names():
    """
    Devuelve la lista de nombres canónicos de plantas termoeléctricas.
    
    Returns:
        list: Lista de nombres canónicos
    """
    return [p for p in PLANTAS_CANONICAS if p is not None]

def standardize_plant_data(data):
    """
    Estandariza todos los nombres de plantas en una estructura de datos.
    
    Args:
        data (dict): Estructura de datos con información de plantas
        
    Returns:
        dict: La misma estructura con nombres estandarizados
    """
    if not data:
        return data
    
    # Copia para no modificar el original
    result = data.copy()
    
    # Procesar sección 'plantas' (avería, mantenimiento)
    if 'plantas' in result:
        plantas_data = result['plantas']
        
        # Procesar avería
        if 'averia' in plantas_data and plantas_data['averia']:
            for planta in plantas_data['averia']:
                if 'planta' in planta and planta['planta']:
                    canonical = get_canonical_plant_name(planta['planta'])
                    if canonical:  # Solo actualizar si hay un nombre canónico válido
                        planta['planta'] = canonical
        
        # Procesar mantenimiento
        if 'mantenimiento' in plantas_data and plantas_data['mantenimiento']:
            for planta in plantas_data['mantenimiento']:
                if 'planta' in planta and planta['planta']:
                    canonical = get_canonical_plant_name(planta['planta'])
                    if canonical:  # Solo actualizar si hay un nombre canónico válido
                        planta['planta'] = canonical
    
    # Procesar sección 'termoelectricas' si existe
    if 'termoelectricas' in result and result['termoelectricas']:
        for planta in result['termoelectricas']:
            if 'nombre' in planta and planta['nombre']:
                canonical = get_canonical_plant_name(planta['nombre'])
                if canonical:  # Solo actualizar si hay un nombre canónico válido
                    planta['nombre'] = canonical
    
    return result
