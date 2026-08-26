import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import Optional

load_dotenv()

# Esquema estructurado completo para FichaAI
class FichaExtraida(BaseModel):
    modelo: str
    procesador: Optional[str] = None
    ram: Optional[str] = None
    almacenamiento: Optional[str] = None
    pantalla: Optional[str] = None
    camara_principal: Optional[str] = None
    bateria: Optional[str] = None
    precio_oficial: Optional[float] = None
    moneda: str = "USD"
    url_imagen: Optional[str] = None

class GeminiService:
    @staticmethod
    def extraer_ficha_desde_texto(texto_o_modelo: str) -> dict:
        """
        Llama a Gemini AI (gemini-3.6-flash).
        Investiga y estructura la ficha técnica completa incluyendo pantalla, RAM, almacenamiento, 
        cámara, batería y URL de imagen oficial/render oficial.
        """
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY no configurada en las variables de entorno.")

        client = genai.Client(api_key=api_key)
        
        prompt = (
            "Eres el motor de búsqueda y catálogo inteligente de FichaAI, especializado en smartphones y tecnología móvil. "
            "A partir de la entrada del usuario (que puede ser el NOMBRE/MODELO del celular o un TEXTO con especificaciones), "
            "proporciona con máxima exactitud y detalle su Ficha Técnica oficial completa.\n\n"
            "Campos requeridos con formato específico:\n"
            "- 'modelo': Nombre comercial oficial completo (ej: 'Tecno Spark 20 Pro', 'Samsung Galaxy S24 Ultra').\n"
            "- 'procesador': Nombre del chipset/CPU (ej: 'MediaTek Helio G99 Ultimate', 'Snapdragon 8 Gen 3').\n"
            "- 'ram': Memoria RAM disponible (ej: '8 GB / 12 GB RAM').\n"
            "- 'almacenamiento': Memoria interna disponible (ej: '256 GB', '512 GB').\n"
            "- 'pantalla': Tipo, tamaño y tasa de refresco (ej: '6.78\" IPS LCD FHD+ a 120Hz', '6.8\" Dynamic AMOLED 2X 120Hz').\n"
            "- 'camara_principal': Detalle del sensor principal (ej: '108 MP f/1.75 con PDAF', '200 MP f/1.7 OIS').\n"
            "- 'bateria': Capacidad de batería y potencia de carga (ej: '5000 mAh con carga rápida de 33W', '5000 mAh (45W)').\n"
            "- 'precio_oficial': Precio numérico oficial de lanzamiento o referencia en USD (ej: 190.00).\n"
            "- 'moneda': 'USD'.\n"
            "- 'url_imagen': Enlace web directo (HTTPS) a una imagen oficial o render oficial en alta calidad del dispositivo (preferir URLs directas de fabricantes como Samsung, Xiaomi, Tecno, Apple o repositorios oficiales/GSMarena).\n\n"
            f"Entrada del usuario:\n\"\"\"{texto_o_modelo}\"\"\""
        )

        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=FichaExtraida,
            ),
        )

        if response.parsed:
            return response.parsed.model_dump()
        else:
            raise ValueError("No se pudo estructurar la información con la IA.")
