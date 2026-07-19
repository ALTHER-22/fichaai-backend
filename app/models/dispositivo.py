import uuid
from app import db
from sqlalchemy.dialects.postgresql import UUID

class Dispositivo(db.Model):
    __tablename__ = 'dispositivo'

    id_dispositivo        = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre_busqueda       = db.Column(db.String(200), nullable=False)
    fabricante            = db.Column(db.String(100))
    url_oficial           = db.Column(db.Text)
    fecha_ultima_consulta = db.Column(db.DateTime)

    fichas = db.relationship('FichaTecnica', backref='dispositivo', lazy=True)

    def to_dict(self):
        return {
            'id_dispositivo':        str(self.id_dispositivo),
            'nombre_busqueda':       self.nombre_busqueda,
            'fabricante':            self.fabricante,
            'url_oficial':           self.url_oficial,
            'fecha_ultima_consulta': self.fecha_ultima_consulta.isoformat() if self.fecha_ultima_consulta else None
        }