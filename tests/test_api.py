"""Pruebas de contrato locales para la API, sin tráfico hacia DIAN ni 2Captcha."""

import io
import unittest
from unittest.mock import AsyncMock, patch

import httpx
import pandas as pd

import main
from paquetes.excepciones import CufeNotFoundError, ScrapingError


def archivo_excel_valido() -> bytes:
    """Construye en memoria el formato mínimo aceptado por el cargador."""
    dataframe = pd.DataFrame(
        [
            {
                "CUFE/CUDE": "cufe-valido",
                "Tipo de documento": "Factura electrónica",
                "Forma de Pago": "2",
                "Grupo": "Recibido",
                "NIT Emisor": "900123456",
            },
            {
                "CUFE/CUDE": "cufe-ignorado",
                "Tipo de documento": "Nota crédito",
                "Forma de Pago": "1",
                "Grupo": "Pendiente",
                "NIT Emisor": "900123457",
            },
        ]
    )
    contenido = io.BytesIO()
    dataframe.to_excel(contenido, index=False, engine="openpyxl")
    return contenido.getvalue()


class ApiContractTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        main.session_cache.clear()
        self.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=main.app), base_url="http://testserver"
        )

    async def asyncTearDown(self):
        await self.client.aclose()

    async def test_openapi_expone_las_tres_rutas(self):
        respuesta = await self.client.get("/openapi.json")

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()["info"]["title"], "API Consulta CUFE")
        self.assertEqual(
            set(respuesta.json()["paths"]),
            {"/ingreso-archivo-cufes/", "/consulta-masiva-cufes/", "/cufe-individual/{cufe}"},
        )

    async def test_rechaza_archivo_que_no_es_excel(self):
        respuesta = await self.client.post(
            "/ingreso-archivo-cufes/", files={"archivo": ("entrada.csv", b"CUFE", "text/csv")}
        )

        self.assertEqual(respuesta.status_code, 400)
        self.assertIn(".xlsx", respuesta.json()["detail"])

    async def test_carga_excel_y_crea_sesion(self):
        respuesta = await self.client.post(
            "/ingreso-archivo-cufes/",
            files={
                "archivo": (
                    "entrada.xlsx",
                    archivo_excel_valido(),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        cuerpo = respuesta.json()
        self.assertIn("1 CUFEs", cuerpo["message"])
        self.assertEqual(
            main.session_cache[cuerpo["session_id"]]["consultas"],
            [{"cufe": "cufe-valido", "nit": "900123456"}],
        )

    async def test_consulta_masiva_rechaza_sesion_invalida(self):
        respuesta = await self.client.post("/consulta-masiva-cufes/", headers={"session-id": "invalida"})

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.json()["detail"], "Session ID inválido o expirado.")

    async def test_consulta_masiva_devuelve_excel_sin_llamar_servicios_externos(self):
        main.session_cache["sesion-prueba"] = {"consultas": [{"cufe": "cufe-valido", "nit": "900123456"}]}
        resultado = io.BytesIO(b"excel-simulado")

        with patch.object(main.sc, "procesar_y_generar_excel_cufes", AsyncMock(return_value=resultado)) as procesar:
            respuesta = await self.client.post(
                "/consulta-masiva-cufes/", headers={"session-id": "sesion-prueba"}
            )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.content, b"excel-simulado")
        self.assertIn("resultado_consultas_cufes.xlsx", respuesta.headers["content-disposition"])
        procesar.assert_awaited_once_with([{"cufe": "cufe-valido", "nit": "900123456"}])

    async def test_consulta_individual_mapea_resultado_y_errores(self):
        with patch.object(main.fc, "consulta_individual", AsyncMock(return_value={"Cufe": "ok"})):
            exitosa = await self.client.get("/cufe-individual/ok?nit=900123456")
        with patch.object(main.fc, "consulta_individual", AsyncMock(side_effect=CufeNotFoundError("ausente"))):
            no_encontrada = await self.client.get("/cufe-individual/ausente?nit=900123456")
        with patch.object(main.fc, "consulta_individual", AsyncMock(side_effect=ScrapingError("sin conexion"))):
            no_disponible = await self.client.get("/cufe-individual/error?nit=900123456")

        self.assertEqual((exitosa.status_code, exitosa.json()), (200, {"Cufe": "ok"}))
        self.assertEqual(no_encontrada.status_code, 404)
        self.assertEqual(no_disponible.status_code, 503)


if __name__ == "__main__":
    unittest.main()
