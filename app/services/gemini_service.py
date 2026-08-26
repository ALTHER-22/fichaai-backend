import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import Optional

load_dotenv()

# Esquema estructurado definitivo y súper completo para FichaAI
class FichaExtraida(BaseModel):
    modelo: str
    procesador: Optional[str] = None
    ram: Optional[str] = None
    almacenamiento: Optional[str] = None
    pantalla: Optional[str] = None
    camara_principal: Optional[str] = None
    camara_frontal: Optional[str] = None
    bateria: Optional[str] = None
    sistema_operativo: Optional[str] = None
    conectividad: Optional[str] = None
    extras: Optional[str] = None
    precio_oficial: Optional[float] = None
    moneda: str = "USD"
    url_imagen: Optional[str] = None

class GeminiService:
    @staticmethod
    def extraer_ficha_desde_texto(texto_o_modelo: str) -> dict:
        """
        Llama a Gemini AI (gemini-3.6-flash).
        Investiga y estructura la ficha técnica hiper-detallada incluyendo cámaras, batería, OS, y conectividad.
        """
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY no configurada en las variables de entorno.")

        client = genai.Client(api_key=api_key)
        
        prompt = (
            "Eres el motor de búsqueda experto y catálogo de FichaAI, especializado en tecnología móvil. "
            "A partir de la entrada del usuario (que puede ser el NOMBRE/MODELO del celular o un TEXTO con especificaciones), "
            "proporciona con máxima exactitud y detalle su Ficha Técnica oficial y súper completa.\n\n"
            "Campos requeridos con formato específico:\n"
            "- 'modelo': Nombre comercial oficial completo (ej: 'Tecno Spark 20 Pro Plus').\n"
            "- 'procesador': Nombre del chipset/CPU (ej: 'MediaTek Helio G99 Ultimate').\n"
            "- 'ram': Memoria RAM disponible (ej: '8 GB').\n"
            "- 'almacenamiento': Memoria interna disponible (ej: '256 GB').\n"
            "- 'pantalla': Tipo, tamaño y tasa de refresco (ej: '6.78\" AMOLED FHD+ a 120Hz').\n"
            "- 'camara_principal': Detalle del sensor principal trasero (ej: '108 MP f/1.75 con PDAF').\n"
            "- 'camara_frontal': Detalle del sensor frontal para selfies (ej: '32 MP f/2.2 con flash doble').\n"
            "- 'bateria': Capacidad de batería y potencia de carga (ej: '5000 mAh con carga rápida de 33W').\n"
            "- 'sistema_operativo': Versión de Android/iOS de fábrica (ej: 'Android 14 con HIOS 14').\n"
            "- 'conectividad': Redes y conectividad destacada (ej: '4G LTE, Wi-Fi 5, Bluetooth 5.2, NFC').\n"
            "- 'extras': Características premium o de resistencia (ej: 'IP53 resistencia al polvo/agua, huella en pantalla, parlantes estéreo').\n"
            "- 'precio_oficial': Precio numérico oficial de lanzamiento o referencia en USD (ej: 190.00).\n"
            "- 'moneda': 'USD'.\n"
            "- 'url_imagen': Enlace web directo (HTTPS) a una imagen oficial o render oficial en alta calidad del dispositivo (preferir URLs directas de fabricantes oficiales o repositorios como GSMarena).\n\n"
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
