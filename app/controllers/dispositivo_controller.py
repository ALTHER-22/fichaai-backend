from flask import Blueprint, jsonify
from sqlalchemy.orm import joinedload
from app.models.dispositivo import Dispositivo

bp = Blueprint('dispositivos', __name__)

# GET /api/dispositivos/lento (Demostración de consulta N+1 - Lazy Loading)
@bp.route('/dispositivos/lento', methods=['GET'])
def listar_lento():
    # Realiza 1 query para obtener los dispositivos
    dispositivos = Dispositivo.query.all()
    resultado = []
    
    for d in dispositivos:
        # Esto genera 1 query extra de SELECT por cada dispositivo en la lista (N queries en total)
        fichas_list = [f.to_dict() for f in d.fichas]
        dict_disp = d.to_dict()
        dict_disp['fichas'] = fichas_list
        resultado.append(dict_disp)
        
    return jsonify({
        'exito': True,
        'modo': 'lazy_loading (N+1 queries)',
        'datos': resultado
    }), 200

# GET /api/dispositivos/rapido (Optimizado - Eager Loading)
@bp.route('/dispositivos/rapido', methods=['GET'])
def listar_rapido():
    # Realiza solo 1 query con JOIN gracias a joinedload
    dispositivos = Dispositivo.query.options(joinedload(Dispositivo.fichas)).all()
    resultado = []
    
    for d in dispositivos:
        # d.fichas ya está cargado en memoria, no se dispara ninguna query extra
        fichas_list = [f.to_dict() for f in d.fichas]
        dict_disp = d.to_dict()
        dict_disp['fichas'] = fichas_list
        resultado.append(dict_disp)
        
    return jsonify({
        'exito': True,
        'modo': 'eager_loading (1 query con JOIN)',
        'datos': resultado
    }), 200
