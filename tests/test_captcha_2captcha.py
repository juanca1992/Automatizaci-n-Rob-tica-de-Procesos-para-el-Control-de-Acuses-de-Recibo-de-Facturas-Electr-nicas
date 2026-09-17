import json
import os
import unittest
from unittest.mock import patch

import httpx

from paquetes.captcha_2captcha import CaptchaResolutionError, resolver_turnstile_proxyless
from paquetes.excepciones import DianAccessError
from paquetes.funciones_cufes import retry


class CaptchaV2Tests(unittest.IsolatedAsyncioTestCase):
    async def test_crea_tarea_v2_y_devuelve_token(self):
        requests = []

        def responder(request):
            requests.append(request)
            if request.url.path == "/createTask":
                return httpx.Response(200, json={"errorId": 0, "taskId": 17})
            return httpx.Response(
                200,
                json={"errorId": 0, "status": "ready", "solution": {"token": "token-prueba"}, "cost": "0.001"},
            )

        async with httpx.AsyncClient(transport=httpx.MockTransport(responder)) as client:
            solution = await resolver_turnstile_proxyless(
                website_url="https://ejemplo.test/buscar",
                website_key="sitekey-prueba",
                action="buscar",
                api_key="clave-prueba",
                client=client,
                poll_interval_seconds=0,
            )

        self.assertEqual(solution.token, "token-prueba")
        self.assertEqual(solution.task_id, 17)
        task = json.loads(requests[0].content)["task"]
        self.assertEqual(task["type"], "TurnstileTaskProxyless")
        self.assertEqual(task["websiteKey"], "sitekey-prueba")
        self.assertEqual(task["action"], "buscar")

    async def test_error_de_api_no_reintenta_ni_expone_clave(self):
        async def responder(request):
            return httpx.Response(200, json={"errorId": 1, "errorCode": "ERROR_KEY_DOES_NOT_EXIST"})

        async with httpx.AsyncClient(transport=httpx.MockTransport(responder)) as client:
            with self.assertRaisesRegex(CaptchaResolutionError, "ERROR_KEY_DOES_NOT_EXIST"):
                await resolver_turnstile_proxyless(
                    website_url="https://ejemplo.test",
                    website_key="sitekey",
                    api_key="clave-secreta",
                    client=client,
                    poll_interval_seconds=0,
                )

    async def test_bloqueo_transitorio_de_dian_es_reintentable(self):
        error = DianAccessError(403)

        self.assertTrue(error.retryable)
        self.assertIn("HTTP 403", str(error))

    async def test_403_reintenta_hasta_el_limite_de_env(self):
        calls = 0

        @retry()
        async def operation():
            nonlocal calls
            calls += 1
            if calls < 3:
                raise DianAccessError(403)
            return "ok"

        with patch.dict(
            os.environ,
            {"DIAN_MAX_ATTEMPTS": "3", "DIAN_RETRY_BASE_DELAY_SECONDS": "0"},
            clear=False,
        ):
            self.assertEqual(await operation(), "ok")

        self.assertEqual(calls, 3)

    async def test_error_de_captcha_no_hace_reintentos(self):
        calls = 0

        @retry()
        async def operation():
            nonlocal calls
            calls += 1
            raise CaptchaResolutionError("error definitivo")

        with patch.dict(os.environ, {"DIAN_MAX_ATTEMPTS": "4"}, clear=False):
            with self.assertRaises(CaptchaResolutionError):
                await operation()

        self.assertEqual(calls, 1)


if __name__ == "__main__":
    unittest.main()
