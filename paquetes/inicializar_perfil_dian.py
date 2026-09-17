"""Inicializa un Chrome normal y aislado de CARFE, sin enviar CUFEs."""

import asyncio
import os
import subprocess
from pathlib import Path

from playwright.async_api import async_playwright

from .navegador_dian import directorio_perfil


URL_BUSQUEDA = "https://catalogo-vpfe.dian.gov.co/User/SearchDocument"


async def inicializar() -> None:
    profile_dir = directorio_perfil()
    profile_dir.mkdir(parents=True, exist_ok=True)
    executable = os.getenv("CARFE_CHROME_EXECUTABLE", "/opt/google/chrome/chrome")
    port = os.getenv("CARFE_CHROME_CDP_PORT", "9223")
    command = [
        executable,
        f"--user-data-dir={profile_dir}",
        f"--remote-debugging-port={port}",
        "--no-first-run",
        "--no-default-browser-check",
        URL_BUSQUEDA,
    ]
    subprocess.Popen(command, start_new_session=True)
    print("Chrome CARFE se abrió sin --no-sandbox.")
    print("Completa cualquier verificación de Cloudflare y presiona Enter para confirmar el perfil.")
    await asyncio.to_thread(input)

    async with async_playwright() as playwright:
        browser = await playwright.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
        page = browser.contexts[0].pages[0]
        print(f"URL final: {page.url}")
        # No cerrar Chrome: la API reutiliza el contexto persistente por CDP.


if __name__ == "__main__":
    asyncio.run(inicializar())
