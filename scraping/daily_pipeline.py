#!/usr/bin/env python3
"""
Pipeline diario para extraer y procesar información sobre afectaciones eléctricas en Cuba.
"""
import os
import sys
import json
import time
import requests
import pandas as pd
import logging
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import argparse


current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(current_dir)
sys.path.append(project_dir)

from scraping import scrape_article_content
from extract_json import CreateJson

log_dir = os.path.join(project_dir, "logs")
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "pipeline.log")),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("daily_pipeline")


class DailyPipeline:

    def __init__(
        self, api_key, model=None, template_path=None, data_dir="data", days_lookback=1
    ):
        """
        Inicialización del pipeline

        Args:
            api_key (str): API key de fireworks.ai
            model (str): Modelo a utilizar
            template_path (str): Ruta al archivo de plantilla para la extracción
            data_dir (str): Directorio para guardar los datos
            days_lookback (int): Número de días hacia atrás para buscar artículos
        """
        self.api_key = api_key
        self.model = model
        self.template_path = template_path or os.path.join(
            os.path.dirname(__file__), "template.txt"
        )
        self.data_dir = data_dir
        self.days_lookback = days_lookback
        self.today = datetime.now()
        self.date_str = self.today.strftime("%Y-%m-%d")
        os.makedirs(os.path.join(data_dir, "daily", self.date_str), exist_ok=True)
        os.makedirs(os.path.join(data_dir, "processed"), exist_ok=True)
        self.existing_data = self.load_existing_data()
        logger.info(f"Inicializado pipeline para fecha: {self.date_str}")

    def load_existing_data(self):
        """
        Carga los datos de afectaciones ya procesados

        Returns:
            DataFrame con los datos existentes
        """
        logger.info("Cargando datos existentes...")
        try:
            df = pd.read_csv(
                os.path.join(
                    self.data_dir,
                    "raw",
                    "afectaciones_electricas_cubadebate_filter_2025.csv",
                ),
                encoding="utf-8-sig",
            )
            logger.info(f"Datos existentes cargados: {len(df)} registros")
            return df
        except Exception as e:
            logger.warning(
                f"Error al cargar datos existentes: {e}. Se utilizará un DataFrame vacío."
            )
            return pd.DataFrame()

    def get_latest_articles(self, max_pages=5):
        """
        Obtiene los artículos más recientes sobre electricidad

        Args:
            max_pages: Número máximo de páginas a recorrer

        Returns:
            DataFrame con los artículos encontrados
        """
        logger.info(
            f"Iniciando scraping de artículos recientes (últimos {self.days_lookback} días)"
        )

        existing_df = self.existing_data
        existing_urls = (
            set(existing_df["Enlace"].tolist())
            if not existing_df.empty and "Enlace" in existing_df.columns
            else set()
        )

        min_date = (self.today - timedelta(days=self.days_lookback)).strftime(
            "%Y-%m-%d"
        )
        logger.info(f"Buscando artículos desde: {min_date}")

        articles_data = []

        for page_num in range(1, max_pages + 1):
            url = f"http://www.cubadebate.cu/categoria/temas/economia-temas/page/{page_num}/"
            logger.info(f"Revisando página: {url}")

            try:
                response = requests.get(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                    },
                )
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")
                articles = soup.find_all("div", class_=["bigimage_post", "image_post"])

                found_recent = False

                for article in articles:
                    title = article.find("div", class_="title").get_text(strip=True)
                    link = article.find("div", class_="title").a["href"]

                    if link in existing_urls:
                        logger.debug(f"Artículo ya procesado: {title}")
                        continue

                    excerpt = (
                        article.find("div", class_="excerpt").get_text(strip=True)
                        if article.find("div", class_="excerpt")
                        else ""
                    )

                    if any(
                        keyword.lower() in title.lower()
                        or keyword.lower() in excerpt.lower()
                        for keyword in [
                            "eléctrica",
                            "Unión Eléctrica",
                            "apagón",
                            "UNE",
                            "corte de luz",
                            "generación eléctrica",
                            "MW",
                            "Felton",
                            "termoeléctrica",
                        ]
                    ):
                        logger.info(f"Artículo encontrado: {title}")

                        article_content = scrape_article_content(
                            link,
                            {
                                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                            },
                        )
                        if article_content:

                            article_date = article_content.get("Fecha", "").split("T")[
                                0
                            ]
                            if article_date >= min_date:
                                found_recent = True
                                articles_data.append(article_content)
                                logger.info(
                                    f"Artículo agregado: {title} - {article_date}"
                                )
                            else:
                                logger.debug(
                                    f"Artículo demasiado antiguo: {title} - {article_date}"
                                )

                        time.sleep(1)

                if not found_recent and page_num > 1:
                    logger.info(
                        f"No se encontraron más artículos recientes en la página {page_num}. Finalizando."
                    )
                    break

                time.sleep(2)

            except Exception as e:
                logger.error(f"Error en página {page_num}: {e}")
                continue

        new_articles_df = pd.DataFrame(articles_data)

        if not new_articles_df.empty:
            daily_dir = os.path.join(self.data_dir, "daily")
            os.makedirs(daily_dir, exist_ok=True)

            daily_file = os.path.join(daily_dir, f"articulos_{self.date_str}.csv")
            new_articles_df.to_csv(daily_file, index=False, encoding="utf-8-sig")
            logger.info(
                f"Se encontraron {len(new_articles_df)} artículos nuevos. Guardados en {daily_file}"
            )

            updated_df = pd.concat([new_articles_df, existing_df], ignore_index=True)
            updated_df.to_csv(
                os.path.join(
                    self.data_dir,
                    "raw",
                    "afectaciones_electricas_cubadebate_filter_2025.csv",
                ),
                index=False,
                encoding="utf-8-sig",
            )
            logger.info(
                f"raw/afectaciones_electricas_cubadebate_filter_2025.csv actualizado"
            )
        else:
            logger.info("No se encontraron artículos nuevos hoy.")

        return new_articles_df

    def process_new_articles(self, articles_df):
        """
        Procesa los artículos nuevos y los guarda en archivos diarios

        Args:
            articles_df (pandas.DataFrame): DataFrame con los artículos a procesar

        Returns:
            bool: True si se procesaron artículos, False si no
        """
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            logger.info(f"Creado directorio: {self.data_dir}")

        if articles_df.empty:
            return 2

        self._process_and_save_day(articles_df)

        self.update_main_json()
        return True

    def update_main_json(self):
        """
        Actualiza el archivo JSON principal con los nuevos datos extraídos
        de todos los días dentro del rango de days_lookback
        """
        main_json_path = os.path.join(
            self.data_dir, "processed", "datos_electricos_organizados.json"
        )
        daily_dir = os.path.join(
            self.data_dir, "daily", self.today.strftime("%Y-%m-%d")
        )
        json_processed = os.path.join(daily_dir, "datos_electricos_organizados.json")

        os.makedirs(os.path.join(self.data_dir, "processed"), exist_ok=True)

        if not os.path.exists(json_processed):
            logger.warning(
                f"No se encontró el archivo JSON procesado en {json_processed}"
            )
            logger.info("Buscando directamente en el directorio del día actual...")

            # Buscar si existe el JSON en el directorio del día actual (nombre generado por CreateJson)
            json_files = [f for f in os.listdir(daily_dir) if f.endswith(".json")]
            if not json_files:
                logger.error("No se encontraron archivos JSON para actualizar")
                return False

            # Usar el primer JSON encontrado
            json_processed = os.path.join(daily_dir, json_files[0])
            logger.info(f"Se utilizará el archivo: {json_processed}")

        # Cargar datos principales si existen
        if os.path.exists(main_json_path):
            try:
                with open(main_json_path, "r", encoding="utf-8") as f:
                    main_data = json.load(f)
                logger.info(f"Cargado archivo JSON principal desde {main_json_path}")
            except Exception as e:
                logger.error(f"Error al cargar el archivo principal: {e}")
                main_data = {}
        else:
            main_data = {}
            logger.warning("No se encontró archivo JSON principal. Creando uno nuevo.")

        try:
            with open(json_processed, "r", encoding="utf-8") as f:
                new_data = json.load(f)
            logger.info(f"Cargado archivo JSON nuevo desde {json_processed}")
            existing_df = self.existing_data
            existing_urls = (
                set(existing_df["Enlace"].tolist())
                if not existing_df.empty and "Enlace" in existing_df.columns
                else set()
            )
            items_added = 0

            for year, months in new_data.items():
                if year not in main_data:
                    main_data[year] = {}

                for month, items in months.items():
                    if month not in main_data[year]:
                        main_data[year][month] = []

                    for item in items:
                        # Verificar si el enlace ya existe en los datos existentes
                        if isinstance(item, dict) and "enlace" in item:
                            if item["enlace"] not in existing_urls:
                                main_data[year][month].append(item)
                                items_added += 1
                        else:
                            logger.warning(f"Elemento no válido o sin enlace: {item}")
                            continue

                        # Solo agregar si el enlace no está en los datos existentes

            logger.info(
                f"Se agregaron {items_added} elementos nuevos al JSON principal"
            )

            try:
                with open(main_json_path, "w", encoding="utf-8") as f:
                    json.dump(main_data, f, ensure_ascii=False, indent=2)
                logger.info(f"Archivo JSON principal actualizado en {main_json_path}")

                processed_path = os.path.join(
                    self.data_dir, "processed", "datos_electricos_organizados.json"
                )
                with open(processed_path, "w", encoding="utf-8") as f:
                    json.dump(main_data, f, ensure_ascii=False, indent=2)
                logger.info(f"Copia del JSON guardada en {processed_path}")

                return True
            except Exception as e:
                logger.error(f"Error al guardar el archivo JSON principal: {e}")
        except Exception as e:
            logger.error(f"Error al procesar el archivo JSON nuevo: {e}")

        return False

    def _process_and_save_day(self, df, date_str=None):
        """
        Procesa los artículos de un día específico usando el extractor JSON

        Args:
            df (pandas.DataFrame): DataFrame con los artículos a procesar
            date_str (str): Fecha en formato YYYY-MM-DD

        Returns:
            bool: True si el proceso fue exitoso, False en caso contrario
        """
        if df.empty:
            logger.info(f"No hay artículos para procesar")
            return False

        logger.info(f"Procesando {len(df)} artículos con el extractor JSON")

        try:
            os.makedirs(
                os.path.join(self.data_dir, "daily", self.today.strftime("%Y-%m-%d")),
                exist_ok=True,
            )
            daily_output_dir = os.path.join(
                self.data_dir, "daily", self.today.strftime("%Y-%m-%d")
            )
            os.makedirs(daily_output_dir, exist_ok=True)

            temp_csv_path = os.path.join(
                daily_output_dir, f"temp_articulos_{str(self.today)}.csv"
            )
            df.to_csv(temp_csv_path, index=False)

            extractor = CreateJson(
                path_df=temp_csv_path,
                path_template=self.template_path,
                url_llm="https://api.fireworks.ai/inference/v1/chat/completions",
                apikey=self.api_key,
                model=self.model,
                a=2022,  # Año de inicio
                b=2025,  # Año final
            )

            result = extractor.run_pipeline(
                delay=2, output_dir=daily_output_dir, save_individual=False
            )

            if os.path.exists(temp_csv_path):
                os.remove(temp_csv_path)

            if result == 0:
                logger.info(f"Extracción JSON completada con éxito para {self.today}")
                return True
            else:
                logger.error(f"Error durante la extracción JSON para {self.today}")
                return False

        except Exception as e:
            logger.error(f"Error en el procesamiento de artículos de {self.today}: {e}")
            return False

    def run(self, analize_all=False):
        """
        Ejecuta el pipeline completo
        """
        if not analize_all:
            logger.info(f"Iniciando pipeline con lookback de {self.days_lookback} días")

            articles = self.get_latest_articles()

            if articles.empty:
                logger.warning(
                    f"No se encontraron nuevos artículos en los últimos {self.days_lookback} días"
                )
                result = self.process_new_articles(articles)
                if isinstance(result, int) and result == 2:
                    logger.info("No hay artículos previos pendientes de procesar")
                    return 2

                logger.info("Se procesaron artículos de días previos")
                return True

            logger.info(
                f"Se encontraron {len(articles)} artículos nuevos para procesar"
            )

            self.process_new_articles(articles)

            logger.info("Pipeline completado exitosamente")
            return True
        logger.info(
            "iniciando la Creación de los JSON para todos los articulos filtrados"
        )
        path = os.path.join(
            self.data_dir, "raw", "afectaciones_electricas_cubadebate_filter_2025.csv"
        )
        extractor = CreateJson(
            path_df=path,
            path_template=self.template_path,
            url_llm="https://api.fireworks.ai/inference/v1/chat/completions",
            apikey=self.api_key,
            model=self.model,
            a=2022,
            b=2025,
        )
        result = extractor.run_pipeline(
            delay=2, output_dir="data/processed", save_individual=False
        )

        if result == 0:
            logger.info(f"Creación JSON completada con éxito para {path}")
            return True

        logger.error(f"Error durante la creación JSON para {path}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the daily pipeline.")
    parser.add_argument(
        "--days_lookback", type=int, default=1, help="Number of days to look back"
    )
    parser.add_argument(
        "--analize_all", type=bool, default=False, help="Analyze all articles if True"
    )
    from dotenv import load_dotenv

    load_dotenv()
    args = parser.parse_args()

    api_key = os.getenv("FIREWORKS_API_KEY")

    if not api_key:
        logger.error(
            "No se encontró la clave API en las variables de entorno (FIREWORKS_API_KEY)"
        )
        sys.exit(1)

    pipeline = DailyPipeline(
        api_key=api_key,
        model="accounts/fireworks/models/llama-v3p3-70b-instruct",
        template_path="template.json",
        data_dir="data",
        days_lookback=args.days_lookback,
    )

    success = pipeline.run(analize_all=args.analize_all)
    if isinstance(success, int) and success == 2:
        logger.info("No hay archivos nuevos para procesar.")
    elif success:
        logger.info("Pipeline diario completado con éxito")
        sys.exit(0)
    else:
        logger.error("Pipeline diario falló")
        sys.exit(1)
