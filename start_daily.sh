#!/bin/bash
#
# Script para iniciar el monitoreo diario de afectaciones eléctricas
# Uso: ./start_daily_monitoring.sh 
#

# Obtener directorio del script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Crear directorio de logs si no existe
mkdir -p logs

echo "====================================================="
echo "  Iniciando Sistema de Monitoreo Eléctrico Diario"
echo "====================================================="
echo

# Verificar si existe la variable de entorno requerida
if [ -z "$FIREWORKS_API_KEY" ]; then
    echo "ERROR: La variable de entorno FIREWORKS_API_KEY no está definida."
    echo "Por favor configurarla ejecutando:"
    echo "export FIREWORKS_API_KEY='tu-api-key'"
    exit 1
fi


check_dependencies() {
    local missing=0
    
    echo "Verificando dependencias Python..."
    python3 -c "import sys; import pandas; import bs4; import requests" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "ERROR: Faltan dependencias de Python. Por favor ejecutar:"
        echo "pip install pandas requests beautifulsoup4"
        missing=1
    fi
    
    echo "Verificando archivos del proyecto..."
    if [ ! -f "template.json" ]; then
        echo "ERROR: No se encontró el archivo template.json"
        missing=1
    fi
    
    if [ ! -f "scraping/scraping.py" ]; then
        echo "ERROR: No se encontró el archivo scraping/scraping.py"
        missing=1
    fi
    
    if [ ! -f "extract_json.py" ]; then
        echo "ERROR: No se encontró el archivo extract_json.py"
        missing=1
    fi
    
    return $missing
}

# Verificar dependencias
check_dependencies
if [ $? -ne 0 ]; then
    echo
    echo "Corrija los errores anteriores y vuelva a ejecutar el script."
    exit 1
fi

echo "Todas las dependencias verificadas correctamente."
echo

echo "Iniciando monitoreo en segundo plano..."
python3 scraping/daily_pipeline.py > logs/pipeline_$(date +%Y%m%d_%H%M%S).log 2>&1 &

if [ $? -eq 0 ]; then
    echo "Proceso iniciado correctamente!"
    echo "Los resultados se guardarán en el directorio data/"
    echo "Los logs se guardarán en el directorio logs/"
else
    echo "Error al iniciar el proceso. Revise los logs para más detalles."
    exit 1
fi

echo
echo "====================================================="
echo "Para más información, consulte README.md"
echo "=====================================================" 