"""Diagnóstico de sólo lectura para el portal DIAN; no resuelve captcha ni envía CUFEs."""

import asyncio
import json

from playwright.async_api import async_playwright

from .navegador_dian import abrir_contexto_dian


URL_BUSQUEDA = "https://catalogo-vpfe.dian.gov.co/User/SearchDocument"


async def ejecutar_diagnostico() -> dict:
    async with async_playwright() as playwright:
        browser = await abrir_contexto_dian(playwright)
        page = await browser.contexts[0].new_page()
        try:
            response = await page.goto(URL_BUSQUEDA, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(2000)
            widget = page.locator(".cf-turnstile").first
            widget_count = await page.locator(".cf-turnstile").count()
            sitekey = await widget.get_attribute("data-sitekey") if widget_count else None
            action = await widget.get_attribute("data-action") if widget_count else None
            cdata = await widget.get_attribute("data-cdata") if widget_count else None
            return {
                "http_status": response.status if response else None,
                "final_url": page.url,
                "title": await page.title(),
                "turnstile_detected": bool(widget_count),
                "sitekey_detected": bool(sitekey),
                "action_detected": bool(action),
                "cdata_detected": bool(cdata),
            }
        finally:
            await page.close()


if __name__ == "__main__":
    print(json.dumps(asyncio.run(ejecutar_diagnostico()), ensure_ascii=False))
