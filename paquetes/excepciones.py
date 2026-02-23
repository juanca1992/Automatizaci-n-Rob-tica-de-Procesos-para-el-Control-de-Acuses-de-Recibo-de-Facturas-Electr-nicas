class AppError(Exception):
    """Clase base para todas las excepciones personalizadas de la aplicación."""
    def __init__(self, message="Ocurrió un error en la aplicación."):
        self.message = message
        super().__init__(self.message)

class FileProcessingError(AppError):
    """Lanzada cuando hay un error al procesar un archivo de entrada."""
    def __init__(self, filename: str, original_error: Exception):
        message = f"No se pudo procesar el archivo '{filename}': {original_error}"
        super().__init__(message)

class ScrapingError(AppError):
    """Lanzada cuando falla una operación de scraping (ej. timeout, elemento no encontrado)."""
    def __init__(self, message="Error durante la extracción de datos de la página de la DIAN."):
        super().__init__(message)

class DianServiceError(ScrapingError):
    """Lanzada específicamente cuando el servicio de la DIAN no está disponible o responde con un error."""
    def __init__(self, message="El servicio de la DIAN no está disponible o no responde."):
        super().__init__(message)

class CufeNotFoundError(ScrapingError):
    """Lanzada cuando un CUFE específico no se encuentra en el sistema de la DIAN."""
    def __init__(self, cufe: str):
        message = f"El CUFE '{cufe}' no fue encontrado."
        super().__init__(message)

class NitNotFoundError(ScrapingError):
    """Lanzada cuando un NIT específico no se encuentra en el sistema de la DIAN."""
    def __init__(self, nit: str):
        message = f"El NIT '{nit}' no fue encontrado o no arrojó resultados."
        super().__init__(message)

class ReporteError(AppError):
    """Lanzada cuando hay un error al leer o procesar un archivo de reporte (Excel, CSV, etc.)."""
    def __init__(self, message="Error al procesar el archivo de reporte."):
        super().__init__(message)
