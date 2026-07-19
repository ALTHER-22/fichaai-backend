import uuid
from app import db
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import CheckConstraint
from datetime import datetime

class FichaTecnica(db.Model):
    __tablename__ = 'ficha_tecnica'

    id_ficha         = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_dispositivo   = db.Column(UUID(as_uuid=True), db.ForeignKey('dispositivo.id_dispositivo'), nullable=False)
    modelo           = db.Column(db.String(200))
    procesador       = db.Column(db.String(200))
    camara_principal = db.Column(db.String(200))
    almacenamiento   = db.Column(db.String(100))
    precio_oficial   = db.Column(db.Numeric(10, 2))
    moneda           = db.Column(db.String(3), default='USD')
    contenido_raw    = db.Column(db.Text)
    fecha_generacion = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint('precio_oficial > 0', name='ck_precio_positivo'),
    )

    def to_dict(self):
        return {
            'id_ficha':         str(self.id_ficha),
            'id_dispositivo':   str(self.id_dispositivo),
            'modelo':           self.modelo,
            'procesador':       self.procesador,
            'camara_principal': self.camara_principal,
            'almacenamiento':   self.almacenamiento,
            'precio_oficial':   float(self.precio_oficial) if self.precio_oficial else None,
            'moneda':           self.moneda,
            'fecha_generacion': self.fecha_generacion.isoformat()
        }