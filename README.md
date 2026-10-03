# ⚡ FichaAI - Backend API REST & Motor de Inteligencia Artificial

[![Python](https://img.shields.io/badge/Python-3.12%20%7C%203.14-blue?logo=python)](https://www.python.org)
[![Flask](https://img.shields.io/badge/Framework-Flask%203.1-black?logo=flask)](https://flask.palletsprojects.com/)
[![Render](https://img.shields.io/badge/Despliegue-Render%20Cloud-46E3B7?logo=render)](https://render.com)
[![Google Gemini](https://img.shields.io/badge/IA-Google%20Gemini%20API-orange?logo=google)](https://ai.google.dev/)
[![Status](https://img.shields.io/badge/Estado-Producci%C3%B3n%20Activo-brightgreen)](https://fichaai-backend.onrender.com/api/health)

Backend oficial y motor de extracción técnica automatizada para el proyecto **FichaAI**. Combina el catálogo en tiempo real de más de 6,000 modelos de teléfonos inteligentes con modelos avanzados de lenguaje de **Google Gemini** para entregar fichas oficiales precisas, precios MSRP calculados en USD y galerías completas de fotografías HD.

---

## 🌐 Despliegue en la Nube (Producción)

- **URL Base:** `https://fichaai-backend.onrender.com/api`
- **Health Check:** `https://fichaai-backend.onrender.com/api/health`

```bash
# Verificación rápida del estado del servidor
curl -s https://fichaai-backend.onrender.com/api/health
```

---

## 📌 Principales Endpoints de la API

| Método | Endpoint | Descripción | Acceso |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | Estado de salud del servicio | Público |
| `POST` | `/api/fichas/extraer-ia` | Búsqueda y extracción inteligente con IA + GSMArena | Público |
| `GET` | `/api/fichas` | Listado paginado de fichas técnicas registradas | Público |
| `GET` | `/api/fichas/<id>` | Detalle de ficha técnica (con caché en memoria) | Público |
| `POST` | `/api/fichas` | Registro manual de una nueva ficha técnica | Autenticado (JWT) |
| `PATCH` | `/api/fichas/<id>` | Actualización parcial de una ficha existente | Autenticado (JWT) |
| `DELETE` | `/api/fichas/<id>` | Eliminación lógica de una ficha | Autenticado (JWT) |

### Ejemplo: Extracción Asistida por IA
```bash
curl -X POST https://fichaai-backend.onrender.com/api/fichas/extraer-ia \
  -H "Content-Type: application/json" \
  -d '{"texto": "Honor Magic 8 Lite"}'
```

---

## 🏗️ Arquitectura del Motor de Extracción

1. **Index Matcher en Vivo:** Consulta el índice en tiempo real de GSMArena para resolver modelos comerciales, variantes y lanzamientos de última generación.
2. **Scraper de Especificaciones:** Extrae la ficha técnica completa y componentes de hardware oficiales.
3. **Galería HD de Estudio:** Selecciona directamente los renders de estudio en alta resolución (700px - 1024px) excluyendo miniaturas de baja resolución.
4. **Traductor y Normalizador con Gemini:** Redacta las especificaciones en un español técnico formal, estructura la salida bajo modelos Pydantic y calcula el precio oficial recomendado de lanzamiento (MSRP) en dólares (USD).
5. **Fallback Generativo:** Si el usuario ingresa un concepto o modelo no listado, el motor genera una ficha técnica coherente garantizando cero caídas de servicio.
