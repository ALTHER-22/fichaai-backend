from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_caching import Cache
from config import Config

db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
jwt = JWTManager()
cache = Cache()

# Función auxiliar para obtener el usuario de la DB y cachear el resultado
@cache.memoize(timeout=300)
def get_user_data_cached(user_id):
    from app.models.usuario import Usuario
    user = Usuario.query.get(user_id)
    if user:
        return {
            'id_usuario': str(user.id_usuario),
            'email': user.email,
            'rol': user.rol
        }
    return None

# Cargador de usuario para Flask-JWT-Extended utilizando el caché
@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    user_data = get_user_data_cached(identity)
    if not user_data:
        return None
    from types import SimpleNamespace
    return SimpleNamespace(**user_data)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    jwt.init_app(app)
    cache.init_app(app)

    # Registro de Blueprints
    from app.controllers.ficha_controller import bp as ficha_bp
    app.register_blueprint(ficha_bp, url_prefix='/api')

    from app.controllers.auth_controller import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api')

    from app.controllers.dispositivo_controller import bp as dispositivo_bp
    app.register_blueprint(dispositivo_bp, url_prefix='/api')

    return app