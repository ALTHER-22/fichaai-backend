"""
Motor de datos reales de FichaAI basado en el catálogo vivo de GSMArena.

Flujo:
1. Descarga (y cachea 6h) el índice completo de teléfonos de GSMArena (~6000 modelos,
   incluye lanzamientos recientes que la IA aún no conoce).
2. Hace coincidencia difusa de la consulta del usuario contra ese índice.
3. Descarga la página oficial del modelo y extrae TODAS las especificaciones.
4. Descarga la galería oficial de fotos del modelo.
"""
import re
import json
import time
import threading
from typing import Optional, List, Dict, Tuple

import requests
from bs4 import BeautifulSoup

BASE = 'https://www.gsmarena.com/'
HEADERS = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/124.0 Safari/537.36'),
    'Accept-Language': 'en-US,en;q=0.9',
}

_session = requests.Session()
_session.headers.update(HEADERS)

_lock = threading.Lock()
_indice: Dict = {'ts': 0, 'makers': {}, 'phones': []}
_cache_fichas: Dict[str, Tuple[float, dict]] = {}
TTL_INDICE = 6 * 3600
TTL_FICHA = 24 * 3600

# Tokens que no definen el modelo (se ignoran al comparar)
TOKENS_NEUTROS = {'5g', '4g', 'lte', 'nfc', 'smartphone', 'celular', 'telefono', 'phone',
                  'movil', 'de', 'el', 'la', 'ficha', 'tecnica', 'specs'}
ALIAS_MARCAS = {'techno': 'tecno', 'tekno': 'tecno', 'iphone': 'apple iphone',
                'redmi': 'xiaomi redmi', 'poco': 'xiaomi poco', 'galaxy': 'samsung galaxy'}


def _normalizar(texto: str) -> List[str]:
    t = (texto or '').lower()
    t = t.replace('+', ' plus ')
    t = re.sub(r'(?<=[a-z])(?=\d)|(?<=\d)(?=[a-z])', ' ', t)  # magic8 -> magic 8
    t = re.sub(r'[^a-z0-9]+', ' ', t)
    return [x for x in t.split() if x]


def _cargar_indice() -> None:
    with _lock:
        if _indice['phones'] and time.time() - _indice['ts'] < TTL_INDICE:
            return
        home = _session.get(BASE, timeout=8)
        m = re.search(r'quicksearch-\d+\.jpg', home.text)
        if not m:
            raise RuntimeError('No se pudo localizar el índice de GSMArena')
        data = json.loads(_session.get(BASE + m.group(0), timeout=10).text)
        makers, phones = data[0], data[1]
        procesados = []
        for p in phones:
            maker = makers.get(str(p[0]), '')
            nombre = p[2]
            alias = p[3] if len(p) > 3 else ''
            alt = p[5] if len(p) > 5 else ''
            nombre_tokens = _normalizar(f'{maker} {nombre}')
            todos = set(nombre_tokens) | set(_normalizar(alias)) | set(_normalizar(alt))
            procesados.append({
                'maker': maker, 'nombre': nombre, 'id': p[1],
                'img': p[4] if len(p) > 4 else '',
                'tokens_nombre': nombre_tokens, 'tokens_todos': todos,
            })
        _indice.update({'ts': time.time(), 'makers': makers, 'phones': procesados})


def buscar_modelo(consulta: str) -> Optional[dict]:
    """Devuelve la mejor coincidencia del catálogo o None si no existe."""
    _cargar_indice()
    q = consulta.lower()
    for k, v in ALIAS_MARCAS.items():
        q = re.sub(rf'\b{k}\b', v, q)
    q_tokens = [t for t in _normalizar(q) if t not in TOKENS_NEUTROS]
    if not q_tokens:
        return None
    marcas = {_normalizar(m)[0] for m in _indice['makers'].values() if _normalizar(m)}

    mejor, mejor_score = None, float('-inf')
    for p in _indice['phones']:
        todos = p['tokens_todos']
        faltan = [t for t in q_tokens if t not in todos]
        # La marca puede omitirse/variar, pero TODO lo demás debe coincidir
        if any(t not in marcas for t in faltan):
            continue
        if faltan and len(faltan) == len(q_tokens):
            continue
        extra = [t for t in p['tokens_nombre'] if t not in q_tokens and t not in TOKENS_NEUTROS]
        score = (len(q_tokens) - len(faltan)) * 10 - len(extra) * 2 - len(faltan) * 3
        if score > mejor_score:
            mejor, mejor_score = p, score
    return mejor


def _slug(p: dict) -> str:
    s = f"{p['maker']} {p['nombre']}".lower()
    s = re.sub(r'[^a-z0-9+]+', '_', s).strip('_')
    return s


def _get(url: str) -> Optional[str]:
    try:
        r = _session.get(url, timeout=8)
        if r.status_code == 200 and 'Turnstile' not in r.text[:3000]:
            return r.text
    except Exception:
        pass
    return None


def _precio(texto: str) -> Tuple[Optional[float], str]:
    if not texto:
        return None, 'USD'
    for simbolo, moneda in (('$', 'USD'), ('€', 'EUR'), ('£', 'GBP'), ('₹', 'INR')):
        m = re.search(re.escape(simbolo) + r'\s*([\d.,]+)', texto)
        if m:
            try:
                return float(m.group(1).replace(',', '')), moneda
            except ValueError:
                pass
    m = re.search(r'About\s+([\d.,]+)\s+(EUR|USD|INR|GBP)', texto)
    if m:
        return float(m.group(1).replace(',', '')), m.group(2)
    return None, 'USD'


def obtener_ficha(consulta: str) -> Optional[dict]:
    """Ficha oficial completa (specs crudas + fotos) o None si el modelo no existe."""
    clave = consulta.strip().lower()
    hit = _cache_fichas.get(clave)
    if hit and time.time() - hit[0] < TTL_FICHA:
        return hit[1]

    p = buscar_modelo(consulta)
    if not p:
        return None

    slug, pid = _slug(p), p['id']
    bigpic = f"https://fdn2.gsmarena.com/vv/bigpic/{p['img']}" if p['img'] else None
    specs: Dict[str, str] = {}
    fotos: List[str] = []

    html = _get(f'{BASE}{slug}-{pid}.php')
    if html:
        soup = BeautifulSoup(html, 'html.parser')
        specs = {t['data-spec']: t.get_text(' ', strip=True) for t in soup.select('[data-spec]')}
        img = soup.select_one('.specs-photo-main img')
        if img and img.get('src'):
            bigpic = img['src']
        link = soup.select_one('.specs-photo-main a')
        pics_url = BASE + link['href'] if link and link.get('href') else f'{BASE}{slug}-pictures-{pid}.php'
        html_pics = _get(pics_url)
        if html_pics:
            s2 = BeautifulSoup(html_pics, 'html.parser')
            for i in s2.select('#pictures-list img'):
                src = i.get('src') or i.get('data-src')
                if src and src.startswith('http') and src not in fotos:
                    fotos.append(src)

    # Priorizar SIEMPRE fotografías oficiales en Alta Resolución (HD 700px+):
    # 'bigpic' de GSMArena es una miniatura lateral de solo 160x212 px.
    # NUNCA colocar 'bigpic' de primero si disponemos de fotos HD de la galería oficial.
    if not fotos and bigpic:
        fotos = [bigpic]

    precio, moneda = _precio(specs.get('price', ''))
    ficha = {
        'modelo': f"{p['maker']} {p['nombre']}".strip(),
        'fabricante': p['maker'],
        'gsmarena_id': pid,
        'specs': specs,
        'precio': precio,
        'moneda': moneda,
        'imagenes': fotos[:8],
    }
    _cache_fichas[clave] = (time.time(), ficha)
    return ficha


def mapear_basico(f: dict) -> dict:
    """Mapeo directo (sin IA) a los campos de FichaAI, usado como respaldo."""
    s = f['specs']

    def j(*partes):
        return ', '.join(x for x in partes if x) or None

    return {
        'modelo': s.get('modelname') or f['modelo'],
        'fabricante': f['fabricante'],
        'procesador': j(s.get('chipset'), s.get('cpu')),
        'ram': (s.get('ramsize-hl') + ' GB') if s.get('ramsize-hl') else s.get('internalmemory'),
        'almacenamiento': s.get('internalmemory'),
        'pantalla': j(s.get('displaysize'), s.get('displaytype'), s.get('displayresolution')),
        'camara_principal': j(s.get('cam1modules'), s.get('cam1video')),
        'camara_frontal': j(s.get('cam2modules'), s.get('cam2video')),
        'bateria': j(s.get('batdescription1'), s.get('battype-hl')),
        'sistema_operativo': s.get('os'),
        'conectividad': j(s.get('nettech'), s.get('wlan'), ('Bluetooth ' + s['bluetooth']) if s.get('bluetooth') else None,
                          ('NFC: ' + s['nfc']) if s.get('nfc') else None, s.get('usb')),
        'extras': j(s.get('bodyother'), s.get('sensors'), s.get('colors')),
        'precio_oficial': f['precio'],
        'moneda': f['moneda'],
    }
