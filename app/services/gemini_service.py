import os
import re
import time
import requests
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()

# Cabeceras de navegador para validación de imágenes
HEADERS_HTTP = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'
}

class FichaExtraida(BaseModel):
    modelo: str
    fabricante: Optional[str] = None
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
    imagenes: List[str] = []


# Sesión HTTP persistente con connection pooling para reuso de sockets TLS
session_http = requests.Session()
adapter = requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=20, max_retries=1)
session_http.mount('https://', adapter)
session_http.mount('http://', adapter)
session_http.headers.update(HEADERS_HTTP)

def coincide_generacion(modelo_pedido: str, url_candidata: str) -> bool:
    """
    Garantiza que la URL de imagen pertenezca a la MISMA generación solicitada.
    Por ejemplo, si el usuario pidió '15C' o '15', rechaza fotos de '14C' o '13C'.
    Si el usuario pidió 'S26', rechaza fotos de 'S24' o 'S25'.
    """
    if not url_candidata:
        return False
    url_low = url_candidata.lower()
    
    # Rechazar páginas web que no son archivos de imagen
    if any(ext in url_low for ext in ['.php', '.html', '.htm', '/pictures.php']):
        return False

    # Extraer tokens alfanuméricos relevantes del modelo pedido (ej. '15c', '15', '26', 's26', '60')
    tokens_modelo = re.findall(r'\b\d+[a-z]?\b|\b[a-z]\d+\b', modelo_pedido.lower())
    
    for tok in tokens_modelo:
        digitos = re.search(r'\d+', tok)
        if not digitos:
            continue
        val = int(digitos.group(0))
        # Generaciones anteriores que suelen infiltrarse indebidamente
        for ant in [val - 1, val - 2, val - 3]:
            if ant <= 0:
                continue
            ant_tok = tok.replace(str(val), str(ant))
            if f"-{ant_tok}" in url_low or f"/{ant_tok}" in url_low or f"_{ant_tok}" in url_low:
                return False
            if f"-{ant}-" in url_low or f"/{ant}-" in url_low or f"-{ant}." in url_low:
                return False
    return True


def verificar_url_imagen_hd(url: str, modelo_pedido: Optional[str] = None) -> tuple:
    """
    Verifica si la URL responde HTTP 200 y retorna (url, content_length_bytes).
    Usa la sesión compartida para evitar handshakes TLS repetitivos.
    """
    if not url or not url.startswith('http'):
        return (None, 0)
    url_lower = url.lower()
    if any(ext in url_lower for ext in ['.php', '.html', '.htm', '/pictures.php']):
        return (None, 0)
    if modelo_pedido and not coincide_generacion(modelo_pedido, url):
        return (None, 0)

    try:
        r = session_http.head(url, timeout=1.5, allow_redirects=False)
        if r.status_code == 200:
            ctype = r.headers.get('Content-Type', '').lower()
            content_length = int(r.headers.get('Content-Length', '0'))
            if 'image' in ctype or any(ext in url_lower for ext in ['.jpg', '.png', '.webp', '.jpeg']):
                if content_length >= 15000 or (content_length == 0 and 'pics/' in url):
                    return (url, content_length)
    except Exception:
        pass
    return (None, 0)


def resolver_galeria_smartphone(fabricante: Optional[str], modelo: str, url_candidata: Optional[str] = None) -> List[str]:
    """
    Motor de resolución de galería oficial HD multi-ángulo ultrarrápido (< 1.5s).
    Aplica Generation Guard: NUNCA permite fotos de generaciones anteriores (ej. 14C para 15C).
    """
    fab_clean = re.sub(r'[^a-z0-9]+', '', (fabricante or '').lower())
    mod_clean = re.sub(r'[^a-z0-9]+', '-', modelo.lower()).strip('-')

    slugs = []
    # 1. Si la IA proporcionó una URL candidata directa que coincida con la generación
    if url_candidata and coincide_generacion(modelo, url_candidata):
        m1 = re.search(r'vv/(?:bigpic|pics/([^/]+))/([^/]+?)(?:-\d+)?\.jpg', url_candidata)
        m2 = re.search(r'gsmarena\.com/([^/]+)-\d+\.php', url_candidata)
        if m1:
            if m1.group(1) and not fab_clean:
                fab_clean = m1.group(1)
            slugs.append(m1.group(2))
        elif m2:
            slugs.append(m2.group(1).replace('_', '-'))

    # 2. Slugs naturales basados en el modelo y fabricante
    if mod_clean and mod_clean not in slugs:
        slugs.append(mod_clean)
    if fab_clean and not mod_clean.startswith(fab_clean):
        comb = f"{fab_clean}-{mod_clean}"
        if comb not in slugs:
            slugs.append(comb)

    # Submarcas
    if 'poco' in mod_clean and 'xiaomi' not in mod_clean:
        slugs.append(f"xiaomi-{mod_clean}")
    if 'redmi' in mod_clean and 'xiaomi' not in mod_clean:
        slugs.append(f"xiaomi-{mod_clean}")

    # Determinar marcas objetivo precisas (máximo 1 o 2)
    brands = [fab_clean] if fab_clean else []
    if fab_clean in ['poco', 'redmi']:
        brands.append('xiaomi')
    if not brands:
        for b_kw in ['samsung', 'apple', 'xiaomi', 'infinix', 'tecno', 'honor',
                      'motorola', 'realme', 'vivo', 'oppo', 'google', 'nothing',
                      'oneplus', 'huawei', 'zte', 'nokia', 'sony']:
            if b_kw in mod_clean:
                brands.append(b_kw)
                break
    if not brands:
        brands = ['samsung', 'xiaomi', 'apple', 'infinix', 'tecno']

    candidatas_hd = []
    if url_candidata and 'pics/' in url_candidata and coincide_generacion(modelo, url_candidata):
        candidatas_hd.append(url_candidata)

    for b in brands:
        for s in slugs[:3]:
            for n in range(1, 5):
                cand = f"https://fdn2.gsmarena.com/vv/pics/{b}/{s}-{n}.jpg"
                if coincide_generacion(modelo, cand):
                    candidatas_hd.append(cand)
                if '-5g' not in s and ('s24' in s or 's25' in s or 's26' in s or 'pro' in s):
                    cand_5g = f"https://fdn2.gsmarena.com/vv/pics/{b}/{s}-5g-{n}.jpg"
                    if coincide_generacion(modelo, cand_5g):
                        candidatas_hd.append(cand_5g)

    candidatas_hd_unicas = list(dict.fromkeys(candidatas_hd))[:16]

    fotos_hd = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(verificar_url_imagen_hd, u, modelo): u for u in candidatas_hd_unicas}
        for f in as_completed(futures):
            url_ok, cl = f.result()
            if url_ok:
                fotos_hd.append((url_ok, cl))

    fotos_hd.sort(key=lambda x: x[1], reverse=True)
    vistas = set()
    fotos_hd_unicas = []
    for u, _ in fotos_hd:
        if u not in vistas:
            vistas.add(u)
            fotos_hd_unicas.append(u)

    if len(fotos_hd_unicas) >= 1:
        return fotos_hd_unicas[:5]

    # Fallback si no hubo fotos HD: verificar url_candidata directa con filtro de generación
    if url_candidata and coincide_generacion(modelo, url_candidata):
        u_ok, _ = verificar_url_imagen_hd(url_candidata, modelo)
        if u_ok:
            return [u_ok]

    # Fallback bigpic oficial si existe para esta generación
    for b in brands:
        for s in slugs[:2]:
            bigpic_url = f"https://fdn2.gsmarena.com/vv/bigpic/{s}.jpg"
            if coincide_generacion(modelo, bigpic_url):
                u_ok, _ = verificar_url_imagen_hd(bigpic_url, modelo)
                if u_ok:
                    return [u_ok]

    return []


class GeminiService:
    @staticmethod
    def extraer_ficha_desde_texto(texto_o_modelo: str) -> dict:
        """
        Llama a Gemini AI con instrucciones estrictas de fidelidad y veracidad.
        Investiga especificaciones oficiales, hardware/software exacto del modelo pedido y galería multi-foto.
        """
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY no configurada en las variables de entorno.")

        client = genai.Client(api_key=api_key)

        prompt = (
            "Eres el motor de búsqueda experto y catálogo tecnológico oficial de FichaAI.\n\n"
            "REGLAS OBLIGATORIAS DE IDENTIDAD, FIDELIDAD Y GENERACIÓN:\n"
            "1. FIDELIDAD ABSOLUTA AL NOMBRE Y NÚMERO DE GENERACIÓN:\n"
            "   - Debes mantener EXACTAMENTE el nombre comercial oficial y el número de generación que el usuario solicitó.\n"
            "   - Si el usuario pide 'Xiaomi Redmi 15C', el campo 'modelo' DEBE SER 'Xiaomi Redmi 15C'. ESTÁ ESTRICTAMENTE PROHIBIDO DEGRADARLO O CAMBIARLO A 'Redmi 14C' o generaciones anteriores.\n"
            "   - Si el usuario pide 'Samsung S26 Fan Edition', el campo 'modelo' DEBE SER 'Samsung Galaxy S26 Fan Edition' (o 'Samsung Galaxy S26 FE'). NUNCA degradarlo a 'S24 FE' o 'S25'.\n"
            "   - Aplica esta misma regla de fidelidad a CUALQUIER marca y modelo (Apple, Motorola, Infinix, Tecno, Xiaomi, Samsung, Honor, Realme, Google, etc.).\n"
            "   - Para modelos de generación reciente o próxima, proyecta las especificaciones oficiales correspondientes a esa generación (hardware actualizado: procesador de nueva generación, software como Android 15/16 con HyperOS 2 / One UI 8, batería y cámaras evolucionadas).\n\n"
            "2. REGLA ESTRICTA DE IMÁGENES:\n"
            "   - 'url_imagen': Debe ser EXCLUSIVAMENTE un enlace directo a archivo de imagen (.jpg, .jpeg, .png, .webp). NUNCA enlaces a páginas web (.php, .html).\n"
            "   - La imagen DEBE corresponder a la generación solicitada. ESTRICTAMENTE PROHIBIDO devolver fotos de modelos o generaciones anteriores (ej: si piden 15C, NUNCA devuelvas enlaces de 14C; si piden S26, NUNCA devuelvas enlaces de S24/S25).\n"
            "   - Si no existe un render o foto de prensa oficial certero para esa generación específica, asigna null en 'url_imagen'.\n\n"
            "3. Datos Verídicos y Oficiales Requeridos:\n"
            "   - 'modelo': Nombre comercial oficial completo exacto.\n"
            "   - 'fabricante': Marca oficial (ej: 'Xiaomi', 'Samsung', 'Apple', 'Infinix', 'Tecno', 'Motorola').\n"
            "   - 'procesador': Nombre exacto del SoC de fábrica (ej: 'MediaTek Helio G91 Ultra', 'Snapdragon 8 Gen 5', 'Qualcomm Snapdragon 8 Gen 3').\n"
            "   - 'ram': RAM oficial (ej: '8 GB', '12 GB', '16 GB').\n"
            "   - 'almacenamiento': Opciones oficiales de memoria (ej: '128 GB / 256 GB').\n"
            "   - 'pantalla': Tipo, tamaño en pulgadas, resolución y tasa de refresco.\n"
            "   - 'camara_principal': Detalle de sensores traseros con MP y apertura.\n"
            "   - 'camara_frontal': Sensor frontal selfie.\n"
            "   - 'bateria': Capacidad en mAh y velocidad de carga en Watts.\n"
            "   - 'sistema_operativo': Versión de SO de fábrica (ej: 'Android 15 con HyperOS 2', 'Android 16 con One UI 8').\n"
            "   - 'conectividad': Redes y conectividad (ej: '5G, Wi-Fi 7, Bluetooth 5.4, NFC, USB-C').\n"
            "   - 'extras': Certificación IP, lector de huellas y funciones clave.\n"
            "   - 'precio_oficial': Precio numérico oficial de referencia o lanzamiento en USD.\n"
            "   - 'moneda': 'USD'.\n\n"
            f"Entrada del usuario a investigar:\n\"\"\"{texto_o_modelo}\"\"\""
        )

        modelos_config = [
            ('gemini-3.5-flash-lite', None),
            ('gemini-3.5-flash', types.ThinkingConfig(thinking_budget=0)),
        ]
        ultimo_error = None

        for modelo_nombre, thinking in modelos_config:
            for intento in range(2):
                try:
                    kwargs = {
                        "response_mime_type": "application/json",
                        "response_schema": FichaExtraida,
                    }
                    if thinking is not None:
                        kwargs["thinking_config"] = thinking

                    response = client.models.generate_content(
                        model=modelo_nombre,
                        contents=prompt,
                        config=types.GenerateContentConfig(**kwargs),
                    )
                    if response.parsed:
                        data = response.parsed.model_dump()

                        # Resolver galería multi-ángulo tipo tienda profesional
                        fab = data.get('fabricante')
                        mod = data.get('modelo') or texto_o_modelo
                        cand = data.get('url_imagen')
                        galeria = resolver_galeria_smartphone(fab, mod, cand)

                        data['imagenes'] = galeria
                        data['url_imagen'] = galeria[0] if galeria else cand

                        return data
                except Exception as e:
                    ultimo_error = e
                    err_str = str(e)
                    if '503' in err_str or 'UNAVAILABLE' in err_str:
                        time.sleep(1.2)
                        continue
                    break

        if ultimo_error:
            raise ultimo_error
        raise ValueError("No se pudo estructurar la información con la IA.")
