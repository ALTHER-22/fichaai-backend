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
    ram              = db.Column(db.String(100))
    almacenamiento   = db.Column(db.String(100))
    pantalla         = db.Column(db.String(200))
    camara_principal = db.Column(db.String(200))
    camara_frontal   = db.Column(db.String(200))
    bateria          = db.Column(db.String(100))
    sistema_operativo= db.Column(db.String(200))
    conectividad     = db.Column(db.String(200))
    extras           = db.Column(db.String(200))
    precio_oficial   = db.Column(db.Numeric(10, 2))
    moneda           = db.Column(db.String(3), default='USD')
    url_imagen       = db.Column(db.Text)
    contenido_raw    = db.Column(db.Text)
    fecha_generacion = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint('precio_oficial > 0', name='ck_precio_positivo'),
    )

    def to_dict(self):
        return {
            'id_ficha':          str(self.id_ficha),
            'id_dispositivo':    str(self.id_dispositivo),
            'modelo':            self.modelo,
            'procesador':        self.procesador,
            'ram':               self.ram,
            'almacenamiento':    self.almacenamiento,
            'pantalla':          self.pantalla,
            'camara_principal':  self.camara_principal,
            'camara_frontal':    self.camara_frontal,
            'bateria':           self.bateria,
            'sistema_operativo': self.sistema_operativo,
            'conectividad':      self.conectividad,
            'extras':            self.extras,
            'precio_oficial':    float(self.precio_oficial) if self.precio_oficial else None,
            'moneda':            self.moneda,
            'url_imagen':        self.url_imagen,
            'fecha_generacion':  self.fecha_generacion.isoformat()
        }