import requests
from bs4 import BeautifulSoup
from typing import Dict


def scrape_article_content(url, headers) -> Dict[str, str]:
    """
    Extrae el contenido de un artículo desde una URL específica.

    Args:
        url: URL del artículo a extraer
        headers: Cabeceras HTTP para la solicitud

    Returns:
        Dict: Diccionario con los datos extraídos del artículo o None si hay error
    """
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        title = (
            soup.find("h2", class_="title").get_text(strip=True)
            if soup.find("h2", class_="title")
            else "No título"
        )

        date = soup.find("time").get("datetime") if soup.find("time") else "No fecha"

        content_div = soup.find("div", class_="note_content")
        if content_div:
            for element in content_div(
                ["script", "style", "iframe", "ins", "header", "footer", "nav"]
            ):
                element.decompose()
            content = " ".join(content_div.stripped_strings)
        else:
            content = "No se pudo extraer contenido"

        tags = []
        taxonomies = soup.find("div", id="taxonomies")
        if taxonomies:
            tags = [a.get_text(strip=True) for a in taxonomies.find_all("a")]

        comment_count = soup.find("span", class_="comment_count")
        num_comments = comment_count.get_text(strip=True) if comment_count else "0"

        return {
            "Título": title,
            "Fecha": date,
            "Contenido": content,
            "Etiquetas": ", ".join(tags),
            "Número de Comentarios": num_comments,
            "Enlace": url,
        }

    except Exception as e:
        print(f"Error al extraer contenido de {url}: {e}")
        return None
