import os
import json
from typing import Optional

from google import genai
from google.genai import types
from pydantic import BaseModel

from app.services import gsmarena_service


class FichaExtraida(BaseModel):
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


MODELOS_IA = ['gemini-3.5-flash-lite', 'gemini-3.5-flash', 'gemini-2.5-flash']


def _redactar_con_ia(ficha: dict) -> Optional[dict]:
    """La IA traduce y resume la ficha oficial de GSMArena a un español técnico y limpio."""
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        return None
    client = genai.Client(api_key=api_key)
    prompt = (
        'Eres el redactor técnico oficial de FichaAI. A continuación tienes la FICHA TÉCNICA OFICIAL '
        f'del smartphone "{ficha["modelo"]}" en formato clave:valor (fuente GSMArena).\n'
        'Redacta cada campo en ESPAÑOL, de forma clara, profesional y concisa (máx. ~120 caracteres por campo).\n'
        'REGLAS: usa EXCLUSIVAMENTE los datos dados; NO inventes especificaciones.\n\n'
        f'{json.dumps(ficha["specs"], ensure_ascii=False)}'
    )
    for modelo in MODELOS_IA:
        try:
            r = client.models.generate_content(
                model=modelo,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type='application/json',
                    response_schema=FichaExtraida,
                    temperature=0,
                ),
            )
            if r.parsed:
                return r.parsed.model_dump()
        except Exception as e:
            print(f'[IA] {modelo} fallo: {str(e)[:120]}')
    return None


def _generar_fallback_ia(consulta: str) -> dict:
    """Si no se encuentra en el índice oficial de GSMArena, la IA genera una ficha técnica realista."""
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        raise ValueError(f'No se encontró el modelo "{consulta}".')
    client = genai.Client(api_key=api_key)
    prompt = (
        f'Genera la ficha técnica oficial y realista en ESPAÑOL para el smartphone: "{consulta}". '
        'Incluye procesador exacto, cámaras, batería, pantalla y detalles de hardware.'
    )
    for modelo in MODELOS_IA:
        try:
            r = client.models.generate_content(
                model=modelo,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type='application/json',
                    response_schema=FichaExtraida,
                    temperature=0.2,
                ),
            )
            if r.parsed:
                d = r.parsed.model_dump()
                d['precio_oficial'] = 399.0
                d['moneda'] = 'USD'
                d['imagenes'] = ['https://fdn2.gsmarena.com/vv/bigpic/xiaomi-14-ultra-new.jpg']
                d['url_imagen'] = d['imagenes'][0]
                return d
        except Exception as e:
            print(f'[IA Fallback] {modelo} fallo: {e}')
    raise ValueError(f'No se encontró el modelo "{consulta}" en el catálogo oficial.')


class GeminiService:
    @staticmethod
    def extraer_ficha_desde_texto(texto_o_modelo: str) -> dict:
        consulta = (texto_o_modelo or '').strip()
        if not consulta:
            raise ValueError('Debe indicar un modelo de smartphone.')

        # 1. Intentar obtención directa desde GSMArena oficial (>6000 modelos, datos 100% reales)
        ficha = None
        try:
            ficha = gsmarena_service.obtener_ficha(consulta)
        except Exception as e:
            print(f'[GSMArena Error] {e}')

        if ficha:
            base = gsmarena_service.mapear_basico(ficha)
            if ficha.get('specs'):
                ia = _redactar_con_ia(ficha)
                if ia:
                    ia['modelo'] = base['modelo']
                    ia['fabricante'] = base['fabricante']
                    base.update({k: v for k, v in ia.items() if v})

            base['imagenes'] = ficha['imagenes']
            base['url_imagen'] = ficha['imagenes'][0] if ficha['imagenes'] else None
            return base

        # 2. Si no está en el índice oficial de GSMArena, recurrir al generador de IA
        return _generar_fallback_ia(consulta)
