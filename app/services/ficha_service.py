from app.models.ficha_tecnica import FichaTecnica
from app.repositories.ficha_repository import FichaRepository

class FichaService:
    """
    Capa de servicio: orquesta la lógica de negocio.
    Habla con el repositorio, nunca directamente con la base de datos.
    """

    @staticmethod
    def obtener_por_id(id_ficha):
        return FichaRepository.obtener_por_id(id_ficha)

    @staticmethod
    def listar_paginado(pagina, limite):
        return FichaRepository.listar_paginado(pagina, limite)

    @staticmethod
    def crear(datos):
        ficha = FichaTecnica(
            modelo=datos.get('modelo'),
            procesador=datos.get('procesador'),
            camara_principal=datos.get('camara_principal'),
            almacenamiento=datos.get('almacenamiento'),
            precio_oficial=datos.get('precio_oficial'),
            moneda=datos.get('moneda', 'USD'),
            contenido_raw=datos.get('contenido_raw'),
            id_dispositivo=datos.get('id_dispositivo')
        )
        return FichaRepository.guardar(ficha)

    @staticmethod
    def actualizar(ficha, datos):
        campos_permitidos = [
            'modelo', 'procesador', 'camara_principal',
            'almacenamiento', 'precio_oficial', 'moneda', 'contenido_raw'
        ]
        for campo in campos_permitidos:
            if campo in datos:
                setattr(ficha, campo, datos[campo])
        return FichaRepository.actualizar(ficha)

    @staticmethod
    def eliminar_logico(ficha):
        FichaRepository.eliminar_logico(ficha)