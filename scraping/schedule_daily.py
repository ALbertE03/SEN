#!/usr/bin/env python3

import subprocess
import sys
import os
import logging
import traceback
from datetime import datetime
from pathlib import Path

current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(current_dir)
log_dir = os.path.join(project_dir, 'logs')
os.makedirs(log_dir, exist_ok=True)


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "scheduler.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("scheduler")

def check_environment():
    """
    Verifica que el entorno esté correctamente configurado
    
    Returns:
        bool: True si el entorno es correcto, False en caso contrario
    """
    if not os.getenv('FIREWORKS_API_KEY'):
        logger.error("No se encontró la clave API en la variable de entorno FIREWORKS_API_KEY")
        return False
    
    required_files = [
        os.path.join(current_dir, "daily_pipeline.py"),
        os.path.join(project_dir, "template.json"),
        os.path.join(current_dir, "scraping.py")
    ]
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            logger.error(f"Archivo requerido no encontrado: {file_path}")
            return False
    
    return True

def run_pipeline():
    """
    Ejecuta el pipeline diario y registra el resultado
    
    Returns:
        bool: True si el pipeline se ejecutó correctamente, False en caso contrario
    """
    if not check_environment():
        return False
    
    pipeline_script = os.path.join(current_dir, "daily_pipeline.py")
    logger.info(f"Usando script: {pipeline_script}")
    

    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"Iniciando ejecución del pipeline en {timestamp}")
        

        os.chdir(project_dir)
        
        result = subprocess.run(
            [sys.executable, pipeline_script],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            logger.info(f"Pipeline ejecutado correctamente (código de salida: {result.returncode})")
            
            output_log = os.path.join(log_dir, f"output_{datetime.now().strftime('%Y%m%d')}.log")
            with open(output_log, 'w', encoding='utf-8') as f:
                if result.stdout:
                    f.write(result.stdout)
                    
            return True
        else:
            logger.error(f"Error ejecutando el pipeline. Código de salida: {result.returncode}")
            if result.stderr:
                logger.error(f"Error detallado:\n{result.stderr}")
                
                error_log = os.path.join(log_dir, f"error_{datetime.now().strftime('%Y%m%d')}.log")
                with open(error_log, 'w', encoding='utf-8') as f:
                    f.write(result.stderr)
                    if result.stdout:
                        f.write("\n\n--- Salida estándar ---\n\n")
                        f.write(result.stdout)
            
            return False
            
    except Exception as e:
        logger.error(f"Excepción ejecutando el pipeline: {e}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logger.info("=== Iniciando ejecución programada ===")
    
    try:
        success = run_pipeline()
        
        if success:
            logger.info("=== Ejecución completada con éxito ===")
            sys.exit(0)
        else:
            logger.error("=== La ejecución falló ===")
            sys.exit(1)
    except Exception as e:
        logger.critical(f"Error crítico en el scheduler: {e}")
        logger.critical(traceback.format_exc())
        sys.exit(2) 