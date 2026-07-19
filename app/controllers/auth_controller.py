from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token
from app import db, bcrypt
from app.models.usuario import Usuario

bp = Blueprint('auth', __name__)

# REGISTER - POST /api/auth/registro
@bp.route('/auth/registro', methods=['POST'])
def registro():
    data = request.get_json(silent=True) or {}
    email = data.get('email')
    password = data.get('password')
    rol = data.get('rol', 'user')

    if not email or not password:
        return jsonify({'exito': False, 'mensaje': 'El email y el password son obligatorios'}), 400

    # Validar si el usuario ya existe
    usuario_existente = Usuario.query.filter_by(email=email).first()
    if usuario_existente:
        return jsonify({'exito': False, 'mensaje': 'El email ya está registrado'}), 400

    # Crear nuevo usuario
    password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    nuevo_usuario = Usuario(
        email=email,
        password_hash=password_hash,
        rol=rol
    )

    try:
        db.session.add(nuevo_usuario)
        db.session.commit()
        return jsonify({
            'exito': True,
            'datos': nuevo_usuario.to_dict(),
            'mensaje': 'Usuario registrado exitosamente'
        }), 201
    except Exception:
        db.session.rollback()
        return jsonify({'exito': False, 'mensaje': 'Error al registrar el usuario'}), 500


# LOGIN - POST /api/auth/login
@bp.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'exito': False, 'mensaje': 'El email y el password son obligatorios'}), 400

    usuario = Usuario.query.filter_by(email=email).first()
    if not usuario or not bcrypt.check_password_hash(usuario.password_hash, password):
        return jsonify({'exito': False, 'mensaje': 'Credenciales incorrectas'}), 401

    # Generar tokens
    access_token = create_access_token(identity=str(usuario.id_usuario))
    refresh_token = create_refresh_token(identity=str(usuario.id_usuario))

    return jsonify({
        'exito': True,
        'token_acceso': access_token,
        'token_actualizacion': refresh_token,
        'datos': usuario.to_dict()
    }), 200
