from fastapi import FastAPI, UploadFile, File, HTTPException, Header
from fastapi.responses import JSONResponse, Response
from tempfile import NamedTemporaryFile
from cachetools import TTLCache
import uuid
import paquetes.funciones_cufes as fc
import paquetes.servicio_cufe as sc
import os
from paquetes.lector_reportes import leer_consultas_desde_excel
from paquetes.excepciones import ScrapingError, CufeNotFoundError, ReporteError
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="API Consulta CUFE")

session_cache = TTLCache(maxsize=1000, ttl=3600)

@app.post("/ingreso-archivo-cufes/", tags=["CUFE"])
async def ingreso_archivo_cufes(archivo: UploadFile = File(...)):
    if not archivo.filename.endswith('.xlsx'):
        raise HTTPException(status_code=400, detail="Formato de archivo no válido. Por favor, suba un archivo .xlsx")

    temp_file_path = None
    try:
        with NamedTemporaryFile(delete=False, mode='wb', suffix=".xlsx") as temp_file:
            temp_file_path = temp_file.name
            temp_file.write(await archivo.read())

        consultas = leer_consultas_desde_excel(temp_file_path)
        session_id = str(uuid.uuid4())
        session_cache[session_id] = {"consultas": consultas}

        return JSONResponse(
            content={
                "message": f"Archivo procesado con éxito. Se encontraron {len(consultas)} CUFEs para consultar.",
                "session_id": session_id
            },
            status_code=200
        )
    except ReporteError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Ocurrió un error interno al procesar el archivo.")
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)


@app.post("/consulta-masiva-cufes/", tags=["CUFE"])
async def consultar_cufes_masivo(session_id: str = Header(...)):
    session_data = session_cache.get(session_id)
    if not session_data:
        raise HTTPException(status_code=400, detail="Session ID inválido o expirado.")

    consultas = session_data.get("consultas")
    if not consultas:
        return JSONResponse(content={"message": "No hay CUFES para consultar."}, status_code=400)
    
    try:
        excel_buffer = await sc.procesar_y_generar_excel_cufes(consultas)
        return Response(
            content=excel_buffer.getvalue(),
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={"Content-Disposition": "attachment; filename=resultado_consultas_cufes.xlsx"}
        )
    except ScrapingError as e:
        raise HTTPException(status_code=503, detail=f"Error al comunicarse con el servicio de la DIAN: {e}")
    except Exception:
        raise HTTPException(status_code=500, detail="Ocurrió un error interno durante la consulta masiva.")

@app.get("/cufe-individual/{cufe}", tags=["CUFE"])
async def consulta_individual_cufe(cufe: str, nit: str):
    try:
        data = await fc.consulta_individual(cufe, nit)
        return JSONResponse(content=data, status_code=200)
    except CufeNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ScrapingError as e:
        raise HTTPException(status_code=503, detail=f"Error al comunicarse con el servicio de la DIAN: {e}")
    except Exception:
        raise HTTPException(status_code=500, detail="Ocurrió un error interno al consultar el CUFE.")
