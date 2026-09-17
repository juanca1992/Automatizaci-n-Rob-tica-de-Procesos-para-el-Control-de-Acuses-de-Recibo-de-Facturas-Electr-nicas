"""Conexión a un Chrome normal y aislado para consultas al portal DIAN."""

from __future__ import annotations

import os
from pathlib import Path

from playwright.async_api import Playwright


def directorio_perfil() -> Path:
    """Perfil exclusivo de CARFE; nunca reutiliza el perfil personal de Chrome."""
    configured = os.getenv("CARFE_BROWSER_PROFILE_DIR", ".carfe-browser-profile")
    return Path(configured).expanduser().resolve()


async def abrir_contexto_dian(playwright: Playwright):
    """Se conecta al Chrome CARFE ya abierto, sin lanzar Chrome con Playwright."""
    cdp_url = os.getenv("CARFE_CHROME_CDP_URL", "http://127.0.0.1:9223")
    try:
        browser = await playwright.chromium.connect_over_cdp(cdp_url)
    except Exception as error:
        raise RuntimeError(
            "Chrome CARFE no está abierto. Ejecute primero `python -m paquetes.inicializar_perfil_dian`."
        ) from error
    if not browser.contexts:
        raise RuntimeError("Chrome CARFE no expuso un contexto de navegador.")
    return browser
