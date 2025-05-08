import requests
import os
import pandas as pd
import json
import time
from pathlib import Path
from typing import Dict, Optional


class CreateJson:
    """
    Clase para extraer y estructurar información de afectaciones eléctricas
    desde textos usando un modelo de lenguaje.
    """

    def __init__(
        self,
        path_df: str,
        path_template: str,
        url_llm: str,
        apikey: str,
        model: str,
        a: int,
        b: int,
    ) -> None:
        """
        Inicializa el extractor de datos para informes de afectaciones eléctricas.

        Args:
            path_df: Ruta al archivo CSV
            path_template: Ruta al archivo de plantilla JSON
            url_llm: URL del API LLM
            apikey: API key para autenticación
            model: ID del modelo a utilizar
            a: Año inicial para guardar la data organizada
            b: Año final para guardar la data organizada

        Raises:
            ValueError: Si a es mayor que b
            FileNotFoundError: Si no se encuentra el archivo de plantilla
            KeyError: Si la estructura del template no es correcta
        """
        if a > b:
            raise ValueError("a tiene que ser menor que b")

        self.df = pd.read_csv(path_df)

        try:
            with open(path_template, "r", encoding="utf-8") as template_file:
                template_data = json.load(template_file)
                self.json_template = json.dumps(
                    template_data["2025"]["enero"][0]["datos"],
                    ensure_ascii=False,
                    indent=4,
                )
        except FileNotFoundError as e:
            raise FileNotFoundError(e)
        except KeyError as e:
            raise KeyError(f"Revise las keys de su template.json: {e}")

        self.url_llm = url_llm
        self.headers = {
            "Authorization": f"Bearer {apikey}",
            "Content-Type": "application/json",
        }
        self.model = model

        self.system_prompt = self._create_system_prompt()

        self.results = []

        self.meses = {
            1: "enero",
            2: "febrero",
            3: "marzo",
            4: "abril",
            5: "mayo",
            6: "junio",
            7: "julio",
            8: "agosto",
            9: "septiembre",
            10: "octubre",
            11: "noviembre",
            12: "diciembre",
        }

        #
        self.organized_data = {
            str(año): {mes: [] for mes in self.meses.values()}
            for año in range(a, b + 1)
        }

    def _create_system_prompt(self) -> str:
        """
        Crea el prompt del sistema con instrucciones detalladas.

        Returns:
            str: Prompt del sistema configurado
        """
        return f"""Extrae información de afectaciones eléctricas y devuelve SÓLO UN OBJETO JSON con esta estructura:
{self.json_template}

Instrucciones específicas:
1. En "zonas_con_problemas": Lista de zonas con problemas eléctricos (array de strings)
2. En "fecha_reporte": Fecha mencionada en el texto
3. En "prediccion": 
   - "disponibilidad": Disponibilidad estimada en MW
   - "demanda_maxima": Demanda máxima estimada en MW
   - "afectacion": Afectación pronosticada en MW
   - "deficit": Déficit estimado en MW
   - "respaldo": Información de respaldo si existe
   - "horario_pico": Hora o periodo del pico de demanda mencionado
4. En "info_matutina":
   - "hora": Hora de la información matutina (ej. "7:00 a.m.")
   - "disponibilidad": Disponibilidad del SEN en MW
   - "demanda": Demanda en ese momento en MW
   - "deficit": Déficit en ese momento en MW
   - "proyeccion_mediodia": Información sobre proyección al mediodía (afectación estimada y hora)
5. En "plantas":
   - "averia": Array de objetos con datos de plantas en avería (planta, unidad/es, tipo)
   - "mantenimiento": Array de objetos con datos de plantas en mantenimiento (planta, unidad/es, tipo)
   - "limitacion_termica": Limitaciones térmicas en MW y tipo
6. En "distribuida":
   - "motores_con_problemas": Objeto con total de centrales/motores con problemas, impacto en MW y causa
   - "problemas_lubricantes": Información sobre problemas de lubricantes (MW afectados, unidades)
   - "patanas_con_problemas": Array de objetos con datos sobre patanas con problemas, incluyendo nombre, motores afectados, MW afectados y recuperación estimada
7. En "paneles_solares":
   - "cantidad_parques": Número de parques solares mencionados
   - "produccion_mwh": Producción en MWh de los parques solares
   - "nuevos_parques": Información sobre nuevos parques solares
   - "capacidad_instalada": Capacidad instalada en MW
   - "periodo_produccion": Período de tiempo al que se refiere la producción
8. En "impacto":
   - "horas_totales": Horas totales de afectación
   - "continuidad_afectacion": Si la afectación ha sido continua o intermitente
   - "maximo": Objeto con datos de afectación máxima (MW, hora, fecha y nota adicional)
   - "tendencia": Tendencia mencionada en la afectación

Para campos desconocidos usa null, no inventes datos. No añadas campos adicionales al JSON."""

    def extract_json_from_text(self, text: str) -> Optional[Dict]:
        """
        Extrae datos estructurados de un texto utilizando LLM.

        Args:
            text: Texto del informe de afectación eléctrica

        Returns:
            Optional[Dict]: Datos estructurados en formato JSON o None si hay error
        """
        try:

            response = requests.post(
                self.url_llm,
                headers=self.headers,
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": text},
                    ],
                    "temperature": 0.1,
                    "max_tokens": 2500,
                    "response_format": {"type": "json_object"},
                },
            )

            if response.status_code != 200:
                print(
                    f"Error en la API (código {response.status_code}): {response.text}"
                )
                return None

            data = response.json()
            if "choices" not in data or not data["choices"]:
                print("La API no devolvió 'choices' válidas:", data)
                return None

            json_str = data["choices"][0]["message"]["content"]
            json_str = json_str.strip()

            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]
            json_str = json_str.strip()

            try:
                json_data = json.loads(json_str)
                return json_data
            except json.JSONDecodeError as e:
                print(f"Error decodificando JSON: {e}")
                print(f"Texto JSON problemático: {json_str[:100]}...")

                try:
                    fixed_str = json_str.replace("'", '"')
                    json_data = json.loads(fixed_str)
                    print("JSON arreglado exitosamente")
                    return json_data
                except:
                    print("No se pudo arreglar el JSON")
                    return None
        except Exception as e:
            print(f"Error procesando texto: {e}")
            return None

    def process_all_reports(
        self, delay: int = 2, output_dir: str = "data", save_individual: bool = False
    ) -> None:
        """
        Procesa todos los informes en el DataFrame.

        Args:
            delay: Tiempo de espera entre llamadas a la API (segundos)
            output_dir: Directorio para guardar los resultados
            save_individual: Si se debe guardar cada informe individualmente
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        self.results = []
        total_informes = len(self.df)

        for i, row in self.df.iterrows():
            print(f"Procesando informe {i+1}/{total_informes}...")

            json_data = self.extract_json_from_text(row["Contenido"])

            if json_data is not None:

                result = {
                    "enlace": row["Enlace"],
                    "fecha": row.get("Fecha", ""),
                    "datos": json_data,
                }
                self.results.append(result)

                if save_individual:
                    individual_file = f'{output_dir}/extracted_row_{row["Fecha"]}.json'
                    with open(individual_file, "w", encoding="utf-8") as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)

            time.sleep(delay)

    def organize_by_date(self) -> None:
        """
        Organiza los resultados por año y mes.
        """
        for result in self.results:
            fecha = result.get("fecha", "")
            try:
                partes_fecha = fecha.split("-")
                if len(partes_fecha) >= 2:
                    año = partes_fecha[0]
                    mes_num = int(partes_fecha[1])

                    mes = self.meses.get(mes_num, "")

                    if año in self.organized_data and mes in self.organized_data[año]:
                        self.organized_data[año][mes].append(result)
            except Exception as e:
                print(f"Error organizando resultado con fecha {fecha}: {e}")

    def save_results(self, output_dir: str = "data") -> None:
        """
        Guarda los resultados en archivos JSON.

        Args:
            output_dir: Directorio para guardar los archivos
        """
        if not any(
            self.organized_data[año][mes]
            for año in self.organized_data
            for mes in self.organized_data[año]
        ):
            self.organize_by_date()

        organized_file = f"{output_dir}/datos_electricos_organizados.json"
        with open(organized_file, "w", encoding="utf-8") as f:
            json.dump(self.organized_data, f, ensure_ascii=False, indent=2)

        print(f"Proceso completado. Datos guardados en {organized_file}")

    def run_pipeline(
        self, delay: int = 2, output_dir: str = "data", save_individual: bool = False
    ) -> int:
        """
        Ejecuta el pipeline completo de procesamiento.

        Args:
            delay: Tiempo de espera entre llamadas a la API (segundos)
            output_dir: Directorio para guardar los resultados
            save_individual: Si se debe guardar cada informe individualmente

        Returns:
            int: Código de resultado (0: éxito, 1: error)
        """
        try:
            self.process_all_reports(delay, output_dir, save_individual)
            self.organize_by_date()
            self.save_results(output_dir)
            return 0
        except Exception as e:
            print(f"Error en el pipeline: {e}")
            return 1


"""if __name__ == "__main__":
    cj = CreateJson(
        path_df='afectaciones_electricas_cubadebate_filter.csv',
        path_template='template.json',
        url_llm="https://api.fireworks.ai/inference/v1/chat/completions",
        apikey=os.getenv('FIREWORKS_API_KEY'),
        model='accounts/fireworks/models/llama-v3p3-70b-instruct',
        a=2022,
        b=2025
    )
    
    check = cj.run_pipeline(delay=2, output_dir='data', save_individual=False) 
    if check == 0:
        print('Proceso completado exitosamente')
    else:
        print("Error durante la ejecución del proceso")"""
