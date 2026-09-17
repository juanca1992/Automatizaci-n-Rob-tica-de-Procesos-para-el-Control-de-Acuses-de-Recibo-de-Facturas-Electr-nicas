import os
import unittest
from unittest.mock import AsyncMock

from paquetes.navegador_dian import abrir_contexto_dian, directorio_perfil


class NavegadorDianTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.previous = dict(os.environ)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.previous)

    def test_perfil_por_defecto_es_aislado(self):
        os.environ.pop("CARFE_BROWSER_PROFILE_DIR", None)
        self.assertEqual(directorio_perfil().name, ".carfe-browser-profile")

    async def test_conecta_al_chrome_aislado_por_cdp(self):
        os.environ["CARFE_CHROME_CDP_URL"] = "http://127.0.0.1:9555"
        browser = type("Browser", (), {"contexts": [object()]})()
        chromium = type("Chromium", (), {"connect_over_cdp": AsyncMock(return_value=browser)})()
        playwright = type("Playwright", (), {"chromium": chromium})()

        context = await abrir_contexto_dian(playwright)

        self.assertIs(context, browser)
        chromium.connect_over_cdp.assert_awaited_once_with("http://127.0.0.1:9555")


if __name__ == "__main__":
    unittest.main()
