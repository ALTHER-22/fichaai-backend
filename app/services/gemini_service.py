import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import Optional

load_dotenv()

# Esquema estructurado de salida esperado para FichaAI
class FichaExtraida(BaseModel):
    modelo: str
    procesador: Optional[str] = None
    camara_principal: Optional[str] = None
    almacenamiento: Optional[str] = None
    precio_oficial: Optional[float] = None
    moneda: str = "USD"

class GeminiService:
    @staticmethod
    def extraer_ficha_desde_texto(texto: str) -> dict:
        """
        Llama a Gemini AI (gemini-3.6-flash) para extraer las especificaciones técnicas 
        desde un texto libre y devolverlo estructurado en JSON.
        """
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY no configurada en las variables de entorno.")

        client = genai.Client(api_key=api_key)
        
        prompt = (
            "Eres un asistente especializado en tecnología y smartphones para la plataforma FichaAI. "
            "Tu tarea es analizar el siguiente texto y extraer con precisión las especificaciones técnicas "
            "del dispositivo móvil.\n\n"
            "Reglas de extracción:\n"
            "- 'modelo': Nombre comercial completo del dispositivo (ej: 'Samsung Galaxy A55 5G').\n"
            "- 'procesador': Nombre del chipset/CPU (ej: 'Exynos 1480', 'Snapdragon 8 Gen 3').\n"
            "- 'camara_principal': Resolución o detalle del sensor principal (ej: '50 MP con OIS').\n"
            "- 'almacenamiento': Capacidad de memoria interna (ej: '256 GB', '128 GB').\n"
            "- 'precio_oficial': Valor numérico del precio exacto si aparece (ej: 449.99). Si no hay precio, dejar null.\n"
            "- 'moneda': Código ISO de 3 letras de la moneda (ej: 'USD', 'EUR'). Por defecto 'USD'.\n\n"
            f"Texto a procesar:\n\"\"\"{texto}\"\"\""
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
            raise ValueError("No se pudo extraer la información estructurada con la IA.")
