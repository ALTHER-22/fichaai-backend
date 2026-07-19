import uuid
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import cache
from app.services.ficha_service import FichaService
from app.services.worker import enqueue_task

bp = Blueprint('fichas', __name__)

# CREATE - POST /api/fichas
@bp.route('/fichas', methods=['POST'])
@jwt_required()
def crear_ficha():
    data = request.get_json(silent=True)

    if not data or not data.get('id_dispositivo'):
        return jsonify({'exito': False, 'mensaje': 'El campo id_dispositivo es obligatorio'}), 400

    try:
        uuid.UUID(data.get('id_dispositivo'))
    except (ValueError, TypeError):
        return jsonify({'exito': False, 'mensaje': 'ID de dispositivo inválido'}), 400

    if 'precio_oficial' in data:
        try:
            precio = float(data['precio_oficial'])
            if precio <= 0:
                return jsonify({'exito': False,
                    'errores': [{'campo': 'precio_oficial',
                                 'mensaje': 'El precio debe ser mayor a 0'}]}), 422
        except (TypeError, ValueError):
            return jsonify({'exito': False, 'mensaje': 'Precio inválido'}), 400

    try:
        ficha = FichaService.crear(data)
        return jsonify({'exito': True, 'datos': ficha.to_dict(),
                        'mensaje': 'Ficha creada correctamente'}), 201
    except Exception:
        return jsonify({'exito': False, 'mensaje': 'Error al crear la ficha'}), 500


# READ - GET /api/fichas (listado paginado)
@bp.route('/fichas', methods=['GET'])
def listar_fichas():
    try:
        pagina = max(1, int(request.args.get('pagina', 1)))
        limite = min(50, max(1, int(request.args.get('limite', 10))))
    except ValueError:
        return jsonify({'exito': False, 'mensaje': 'Parámetros de paginación inválidos'}), 400

    resultado = FichaService.listar_paginado(pagina, limite)
    return jsonify({
        'exito':   True,
        'datos':   [dict(r._mapping) for r in resultado.items],
        'pagina':  pagina,
        'limite':  limite,
        'total':   resultado.total,
        'paginas': resultado.pages
    }), 200


# READ - GET /api/fichas/<id> (detalle - Cache-Aside)
@bp.route('/fichas/<string:id_ficha>', methods=['GET'])
def obtener_ficha(id_ficha):
    try:
        uuid.UUID(id_ficha)
    except ValueError:
        return jsonify({'exito': False, 'mensaje': 'ID de ficha inválido'}), 400

    # Cache-Aside: buscar en caché primero
    cache_key = f"ficha:{id_ficha}"
    ficha_cached = cache.get(cache_key)
    
    if ficha_cached:
        print(f"[CACHE HIT] Ficha {id_ficha} obtenida desde el caché")
        return jsonify({'exito': True, 'datos': ficha_cached, 'cached': True}), 200

    print(f"[CACHE MISS] Ficha {id_ficha} no encontrada en caché, consultando DB")
    ficha = FichaService.obtener_por_id(id_ficha)
    if not ficha:
        return jsonify({'exito': False, 'mensaje': 'Ficha no encontrada'}), 404
    
    ficha_dict = ficha.to_dict()
    # Guardar en caché con TTL de 300 segundos
    cache.set(cache_key, ficha_dict, timeout=300)
    
    return jsonify({'exito': True, 'datos': ficha_dict, 'cached': False}), 200


# UPDATE - PATCH /api/fichas/<id>
@bp.route('/fichas/<string:id_ficha>', methods=['PATCH'])
@jwt_required()
def actualizar_ficha(id_ficha):
    try:
        uuid.UUID(id_ficha)
    except ValueError:
        return jsonify({'exito': False, 'mensaje': 'ID de ficha inválido'}), 400

    ficha = FichaService.obtener_por_id(id_ficha)
    if not ficha:
        return jsonify({'exito': False, 'mensaje': 'Ficha no encontrada'}), 404

    data = request.get_json(silent=True) or {}

    if 'precio_oficial' in data:
        try:
            precio = float(data['precio_oficial'])
            if precio <= 0:
                return jsonify({'exito': False,
                    'errores': [{'campo': 'precio_oficial',
                                 'mensaje': 'El precio debe ser mayor a 0'}]}), 422
        except (TypeError, ValueError):
            return jsonify({'exito': False, 'mensaje': 'Precio inválido'}), 400

    for campo in ['id_ficha', 'id_dispositivo', 'fecha_generacion']:
        data.pop(campo, None)

    ficha_actualizada = FichaService.actualizar(ficha, data)
    
    # Cache-Aside Invalidation: eliminar del caché porque cambió en DB
    cache.delete(f"ficha:{id_ficha}")
    print(f"[CACHE INVALIDATE] Cache eliminado para Ficha: {id_ficha}")

    return jsonify({'exito': True, 'datos': ficha_actualizada.to_dict()}), 200


# DELETE - DELETE /api/fichas/<id>
@bp.route('/fichas/<string:id_ficha>', methods=['DELETE'])
@jwt_required()
def eliminar_ficha(id_ficha):
    try:
        uuid.UUID(id_ficha)
    except ValueError:
        return jsonify({'exito': False, 'mensaje': 'ID de ficha inválido'}), 400

    ficha = FichaService.obtener_por_id(id_ficha)
    if not ficha:
        return jsonify({'exito': False, 'mensaje': 'Ficha no encontrada'}), 404

    FichaService.eliminar_logico(ficha)
    
    # Cache-Aside Invalidation: eliminar del caché
    cache.delete(f"ficha:{id_ficha}")
    print(f"[CACHE INVALIDATE] Cache eliminado por borrado para Ficha: {id_ficha}")

    return '', 204


# ASYNC TASK - POST /api/fichas/<id_ficha>/reporte
@bp.route('/fichas/<string:id_ficha>/reporte', methods=['POST'])
def encolar_reporte(id_ficha):
    try:
        uuid.UUID(id_ficha)
    except ValueError:
        return jsonify({'exito': False, 'mensaje': 'ID de ficha inválido'}), 400

    ficha = FichaService.obtener_por_id(id_ficha)
    if not ficha:
        return jsonify({'exito': False, 'mensaje': 'Ficha no encontrada'}), 404

    # Encolar la tarea en background worker
    enqueue_task('generar_reporte_pdf', {'id_ficha': id_ficha})

    return jsonify({
        'exito': True,
        'mensaje': 'Generacion de reporte PDF encolada correctamente',
        'tarea': 'generar_reporte_pdf'
    }), 202