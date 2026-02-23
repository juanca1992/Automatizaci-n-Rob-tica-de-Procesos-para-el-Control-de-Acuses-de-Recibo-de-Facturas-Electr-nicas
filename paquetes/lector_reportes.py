import pandas as pd
from .excepciones import ReporteError

def leer_cufes_desde_excel(ruta_archivo: str) -> list[str]:
    """
    Lee un archivo de Excel, aplica filtros específicos y extrae los CUFEs de la
    columna 'CUFE/CUDE', devolviéndolos como una lista de strings.

    Args:
        ruta_archivo (str): La ruta completa al archivo de Excel (.xlsx).

    Returns:
        list[str]: Una lista de CUFEs filtrados como cadenas de texto.

    Raises:
        ReporteError: Si el archivo no se encuentra, no es un archivo de Excel válido,
                      si faltan las columnas necesarias para el filtrado, o si no se
                      encuentran CUFEs después de aplicar los filtros.
    """
    columnas_requeridas = ['CUFE/CUDE', 'Tipo de documento', 'Forma de Pago', 'Grupo']
    tipos_documento_validos = ["Factura electrónica de contingencia", "Factura electrónica"]
    formas_pago_validas = ["2","3"]
    grupo_requerido = "Recibido"

    try:
        # Cargar el archivo de Excel en un DataFrame de pandas, forzando todo a string
        df = pd.read_excel(ruta_archivo, dtype=str)

        # 1. Verificar que todas las columnas necesarias existan
        columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
        if columnas_faltantes:
            raise ReporteError(
                f"Faltan las siguientes columnas en el archivo: {', '.join(columnas_faltantes)}. "
                f"Columnas disponibles: {', '.join(df.columns)}"
            )

        # 2. Aplicar los filtros de forma segura
        df_filtrado = df[
            df['Tipo de documento'].isin(tipos_documento_validos) &
            df['Forma de Pago'].isin(formas_pago_validas) &
            (df['Grupo'] == grupo_requerido)
        ]

        # 3. Extraer CUFEs del DataFrame ya filtrado
        if df_filtrado.empty:
            raise ReporteError("No se encontraron registros que coincidan con los filtros aplicados.")
            
        cufes = df_filtrado['CUFE/CUDE'].dropna().astype(str).tolist()
        
        # Limpiar espacios en blanco y eliminar cadenas vacías
        cufes = [cufe.strip() for cufe in cufes if cufe and cufe.strip()]

        if not cufes:
            raise ReporteError("Después de los filtros, no quedaron CUFEs válidos para procesar.")

        return cufes

    except FileNotFoundError:
        raise ReporteError(f"El archivo no fue encontrado en la ruta: {ruta_archivo}")
    except ValueError as e:
        raise ReporteError(f"Error al leer el archivo. Asegúrese de que es un archivo Excel (.xlsx) válido. Detalle: {e}")
    except Exception as e:
        # Captura la ReporteError específica o cualquier otra excepción
        if isinstance(e, ReporteError):
            raise  # Relanza la excepción ReporteError para que sea manejada externamente
        raise ReporteError(f"Ocurrió un error inesperado al procesar el archivo: {e}")

