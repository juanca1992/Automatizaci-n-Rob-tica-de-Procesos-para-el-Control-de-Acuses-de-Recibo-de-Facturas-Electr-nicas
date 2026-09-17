import pandas as pd
import io
from typing import List
import paquetes.funciones_cufes as fc

async def procesar_y_generar_excel_cufes(consultas: List[dict[str, str]]) -> io.BytesIO:
    """
    Orquesta la consulta masiva de CUFEs y genera un archivo Excel en memoria.

    Args:
        consultas: Lista de CUFEs y NITs requeridos por la búsqueda DIAN.

    Returns:
        Un objeto BytesIO con el contenido del archivo Excel.
    """
    # 1. Realizar la consulta masiva en paralelo para obtener los datos
    data = await fc.consulta_cufe_paralelo(consultas)

    # 2. Crear un DataFrame de pandas con los resultados
    df = pd.DataFrame(data)

    # 3. Crear un buffer de memoria para guardar el archivo Excel
    output_buffer = io.BytesIO()

    # 4. Escribir el DataFrame en el buffer en formato Excel
    df.to_excel(output_buffer, index=False, engine='openpyxl')

    # 5. Reposicionar el puntero del buffer al inicio.
    output_buffer.seek(0)

    # 6. Devolver el buffer
    return output_buffer
