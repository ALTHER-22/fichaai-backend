import uuid
from app import db
from sqlalchemy.dialects.postgresql import UUID

class Usuario(db.Model):
    __tablename__ = 'usuario'

    id_usuario    = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email         = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    rol           = db.Column(db.String(50), default='user')

    def to_dict(self):
        return {
            'id_usuario': str(self.id_usuario),
            'email':      self.email,
            'rol':        self.rol
        }
