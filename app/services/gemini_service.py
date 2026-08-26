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
    def extraer_ficha_desde_texto(texto_o_modelo: str) -> dict:
        """
        Llama a Gemini AI (gemini-3.6-flash).
        Si recibe solo el nombre del celular (ej: 'Samsung Galaxy A55'), genera su ficha técnica oficial.
        Si recibe un párrafo largo de especificaciones, lo analiza y extrae estructurado en JSON.
        """
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY no configurada en las variables de entorno.")

        client = genai.Client(api_key=api_key)
        
        prompt = (
            "Eres el motor de búsqueda inteligente de FichaAI, especializado en smartphones y tecnología móvil. "
            "A partir de la entrada del usuario (que puede ser solo el NOMBRE/MODELO del celular o un TEXTO con especificaciones), "
            "proporciona con máxima precisión técnica su Ficha Técnica oficial.\n\n"
            "Reglas de los campos:\n"
            "- 'modelo': Nombre comercial completo oficial (ej: 'Samsung Galaxy A55 5G', 'iPhone 15 Pro Max').\n"
            "- 'procesador': Procesador exacto (ej: 'Samsung Exynos 1480', 'Apple A17 Pro', 'Snapdragon 8 Gen 3').\n"
            "- 'camara_principal': Sensor principal (ej: '50 MP f/1.8 OIS', '48 MP principal').\n"
            "- 'almacenamiento': Capacidad base o habitual (ej: '128 GB', '256 GB / 512 GB').\n"
            "- 'precio_oficial': Precio oficial de lanzamiento o referencia en dólares numérico (ej: 449.00).\n"
            "- 'moneda': Código de moneda 'USD'.\n\n"
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
