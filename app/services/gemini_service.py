import os
import re
import requests
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed

session_http = requests.Session()
session_http.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})

def coincide_generacion(modelo_pedido: str, url: str) -> bool:
    return True

def verificar_url_imagen_hd(url: str, modelo_pedido: Optional[str] = None) -> tuple:
    if not url or not url.startswith('http'):
        return (None, 0)
    url_lower = url.lower()
    if any(ext in url_lower for ext in ['.php', '.html', '.htm', '/pictures.php']):
        return (None, 0)
    try:
        r = session_http.head(url, timeout=1.5, allow_redirects=True)
        if r.status_code == 200:
            ctype = r.headers.get('Content-Type', '').lower()
            content_length = int(r.headers.get('Content-Length', '0'))
            if 'image' in ctype or any(ext in url_lower for ext in ['.jpg', '.png', '.webp', '.jpeg']):
                return (url, content_length)
    except Exception:
        pass
    return (None, 0)

class FichaExtraida(BaseModel):
    existe_en_la_vida_real: bool
    modelo: str
    fabricante: str
    procesador: str
    ram: str
    almacenamiento: str
    pantalla: str
    camara_principal: str
    camara_frontal: str
    bateria: str
    sistema_operativo: str
    conectividad: str
    extras: str
    precio_oficial: float
    moneda: str
    url_gsmarena: Optional[str]

class GeminiService:
    @staticmethod
    def extraer_ficha_desde_texto(texto_o_modelo: str) -> dict:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY no configurada.")

        client = genai.Client(api_key=api_key)
        
        prompt = (
            "Eres el motor de bǧsqueda de FichaAI.\n"
            f"El usuario busca el smartphone: '{texto_o_modelo}'.\n"
            "REGLAS OBLIGATORIAS:\n"
            "1. SI EL MODELO NO EXISTE (ej. 'Infinix 60', 'iPhone 20'), marca 'existe_en_la_vida_real' como false y llena lo demǭs con 'N/A' o 0.\n"
            "2. Si s existe (ej. 'Samsung S24 Ultra', 'Infinix Zero 30'), marca 'existe_en_la_vida_real' como true, y extrae sus especificaciones REALES.\n"
            "3. En 'url_gsmarena' DEBES poner la URL oficial de gsmarena del telefono si la sabes (ej. https://www.gsmarena.com/samsung_galaxy_s24_ultra-12771.php). Si no, null."
        )

        modelos_config = [
            ('gemini-3.5-flash', types.ThinkingConfig(thinking_budget=0)),
            ('gemini-2.5-flash', None),
        ]
        
        ultimo_error = None
        data = None

        for modelo_nombre, thinking in modelos_config:
            try:
                kwargs = {
                    "response_mime_type": "application/json",
                    "response_schema": FichaExtraida,
                }
                if thinking: kwargs["thinking_config"] = thinking

                response = client.models.generate_content(
                    model=modelo_nombre,
                    contents=prompt,
                    config=types.GenerateContentConfig(**kwargs),
                )
                if response.parsed:
                    data = response.parsed.model_dump()
                    break
            except Exception as e:
                ultimo_error = e
                continue
                
        if not data:
            raise ultimo_error or ValueError("Error IA")

        if not data.get('existe_en_la_vida_real'):
            raise ValueError(f"El modelo '{texto_o_modelo}' no existe en el mercado. Por favor verifica el nombre.")

        # Obtener imǭgenes desde GSMArena
        fotos = []
        url_gsmarena = data.get('url_gsmarena')
        if url_gsmarena and url_gsmarena.startswith('http'):
            try:
                from bs4 import BeautifulSoup
                r = session_http.get(url_gsmarena, timeout=3)
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, 'html.parser')
                    img_div = soup.select_one('.specs-photo-main img')
                    if img_div and img_div.get('src'):
                        fotos.append(img_div['src'])
            except:
                pass

        data['imagenes'] = fotos
        data['url_imagen'] = fotos[0] if fotos else None
        
        return data
