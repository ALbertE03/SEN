# Sistema de Monitoreo Diario de Afectaciones Eléctricas

Este sistema automatiza la extracción de información sobre afectaciones eléctricas en Cuba a partir de artículos publicados en CubaDebate, estructurando los datos en formato JSON mediante LLM.

## Características

- **Scraping diario automático** de artículos sobre electricidad
- **Extracción estructurada** de datos mediante LLM (Llama 3.3)
- **Almacenamiento organizado** por año/mes
- **Evita duplicados** mediante control de URLs ya procesadas
- **Registros detallados** del proceso completo
- **Visualización interactiva** con Streamlit

## Visualización de Datos

Se ha implementado un panel de visualización interactivo utilizando Streamlit que permite:

1. **Inicio**: Visualización de los datos del último día disponible en forma de tabla
2. **Déficit**: Análisis y visualización de datos históricos de déficit eléctrico
3. **Disponibilidad**: Análisis y visualización de datos históricos de disponibilidad eléctrica
4. **Comparativas**: Visualizaciones comparativas entre déficit y disponibilidad

## Ejecución de la Aplicación

Para ejecutar la aplicación de visualización:

1. Instalar las dependencias:
```bash
pip install -r requirements.txt
```

2. Ejecutar la aplicación:
```bash
streamlit run Visualizacion/app.py
```

3. La aplicación estará disponible en el navegador en `http://localhost:8501`

## Estructura del Proyecto

```
.
├── data/                        # Directorio de datos
│   ├── daily/                   # Datos organizados por día
│   ├── processed/               # Datos procesados (JSON estructurado)
│   └── raw/                     # Datos crudos (artículos, CSV)
├── scraping/                    # Código de scraping de artículos
├── Visualizacion/               # Aplicación de visualización con Streamlit
│   ├── app.py                   # Punto de entrada de la aplicación
│   ├── Deficit.py               # Módulo de análisis de déficit
│   ├── Disponibilidad.py        # Módulo de análisis de disponibilidad
│   └── mapping.py               # Funciones de mapeo de datos
├── extract_json.py              # Script de extracción JSON con LLM
├── requirements.txt             # Dependencias del proyecto
└── README.md                    # Documentación
├── logs/                        # Logs del sistema
├── scraping/                    # Scripts de scraping
│   ├── __init__.py              # Inicialización del módulo
│   ├── daily_pipeline.py        # Pipeline diario integrado
│   ├── schedule_daily.py        # Programador de ejecución
│   └── scraping.py              # Funciones base de scraping
├── extract_json.py              # Extractor JSON con LLM
├── template.json                # Plantilla para estructura de datos
├── start_daily_monitoring.sh    # Script para iniciar manualmente
└── README.md                    # Este archivo
```

## Requisitos

- Python 3.8+
- Paquetes: requests, beautifulsoup4, pandas, fireworks-ai (o similar)
- API key de Fireworks.ai (o proveedor LLM compatible)

## Instalación

1. Clona este repositorio
2. Instala las dependencias:

```bash
pip install requests beautifulsoup4 pandas
```

3. Configura la variable de entorno con tu API key:

```bash
export FIREWORKS_API_KEY="tu-api-key"
```

## Uso

### Ejecución manual

Para ejecutar el pipeline manualmente:

```bash
./start_daily_monitoring.sh --pages_lookback 4 --analize_all False --a 300 --b 450
```

- `--pages_lookback`: Número de páginas hacia atrás para buscar artículos (por defecto es 1).
- `--analize_all`: Si se debe analizar todos los artículos de data/raw/afectaciones_electricas_cubadebate_filter_2025.csv (por defecto es False).
- `--a`: página inicial para el scraping.
- `--b`: página final para el scraping.
- `si a>b => error`

### Configuración de Ejecución Automática

#### En Linux/Mac (usando cron)

Para configurar la ejecución automática en sistemas Linux o Mac, usaremos `cron`:

1. Abre la terminal y edita el crontab con:

   ```bash
   crontab -e
   ```

2. Añade una línea para ejecutar el script diariamente a las 9:00 AM:

   ```
   0 9 * * * cd /ruta/completa/al/proyecto && ./scraping/schedule_daily.py >> ./logs/cron.log 2>&1
   ```

3. **IMPORTANTE**: Asegúrate de configurar la variable de entorno `FIREWORKS_API_KEY` en el archivo `~/.bashrc` o `~/.profile`:

   ```bash
   echo 'export FIREWORKS_API_KEY="tu-api-key"' >> ~/.bashrc
   source ~/.bashrc
   ```

#### En Windows (usando Programador de tareas)

1. Crea un archivo batch (ej: `run_monitor.bat`) con el siguiente contenido:

   ```bat
   @echo off
   set FIREWORKS_API_KEY=tu-api-key
   cd /d C:\ruta\completa\al\proyecto
   python scraping\schedule_daily.py
   ```

2. Abre el Programador de tareas (Win+R, escribe `taskschd.msc`)

3. Crea una tarea nueva:
   - Nombre: "Monitoreo Eléctrico Diario"
   - Desencadenador: Diario, a las 9:00 AM
   - Acción: Iniciar un programa, selecciona el archivo batch creado

#### En Linux moderno (usando systemd)

1. Crea un archivo de servicio en `/etc/systemd/system/monitoreo-electrico.service`:

   ```ini
   [Unit]
   Description=Monitoreo Diario de Afectaciones Eléctricas
   After=network.target

   [Service]
   Type=oneshot
   ExecStart=/ruta/completa/al/proyecto/scraping/schedule_daily.py
   WorkingDirectory=/ruta/completa/al/proyecto
   Environment="FIREWORKS_API_KEY=tu-api-key"
   User=tu-usuario

   [Install]
   WantedBy=multi-user.target
   ```

2. Crea un temporizador en `/etc/systemd/system/monitoreo-electrico.timer`:

   ```ini
   [Unit]
   Description=Ejecutar Monitoreo Eléctrico Diariamente

   [Timer]
   OnCalendar=*-*-* 09:00:00
   Persistent=true

   [Install]
   WantedBy=timers.target
   ```

3. Activa y habilita el temporizador:

   ```bash
   sudo systemctl enable monitoreo-electrico.timer
   sudo systemctl start monitoreo-electrico.timer
   ```

## Personalización

### Modificar palabras clave de búsqueda

Edita `self.keywords` en la clase `DailyPipeline` dentro de `scraping/daily_pipeline.py`.

### Ajustar la estructura de datos extraídos

Modifica el archivo `template.json` para cambiar los campos que se extraen.

### Cambiar el modelo de LLM

Actualiza el parámetro `model` al inicializar `DailyPipeline`.

## Troubleshooting

- **Error de API key:** Verifica que la variable de entorno FIREWORKS_API_KEY esté configurada correctamente
- **Problemas de conexión:** Revisa tu conexión a internet y posibles bloqueos por parte del sitio web
- **Errores en extracción de datos:** Consulta los logs en `logs/pipeline.log`

## Verificación

Para verificar que la ejecución automática funciona correctamente:

1. Comprueba los archivos de log después del tiempo programado:

   ```bash
   cat logs/scheduler.log
   ```

2. Verifica que se están generando nuevos datos en el directorio `data/daily/`

## Licencia

[MIT License](LICENSE)
