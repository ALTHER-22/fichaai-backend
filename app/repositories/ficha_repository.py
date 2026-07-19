from app import db
from app.models.ficha_tecnica import FichaTecnica

class FichaRepository:
    """
    Capa de repositorio: encapsula todo el acceso a datos (ORM/SQL).
    El servicio nunca habla directamente con el modelo, solo con este repositorio.
    """

    @staticmethod
    def obtener_por_id(id_ficha):
        return FichaTecnica.query.get(id_ficha)

    @staticmethod
    def listar_paginado(pagina, limite):
        return db.session.query(
            FichaTecnica.id_ficha,
            FichaTecnica.modelo,
            FichaTecnica.procesador,
            FichaTecnica.precio_oficial,
            FichaTecnica.moneda,
            FichaTecnica.fecha_generacion
        ).paginate(page=pagina, per_page=limite, error_out=False)

    @staticmethod
    def guardar(ficha):
        db.session.add(ficha)
        db.session.commit()
        return ficha

    @staticmethod
    def actualizar(ficha):
        db.session.commit()
        return ficha

    @staticmethod
    def eliminar_logico(ficha):
        ficha.contenido_raw = '[ELIMINADO]'
        db.session.commit()