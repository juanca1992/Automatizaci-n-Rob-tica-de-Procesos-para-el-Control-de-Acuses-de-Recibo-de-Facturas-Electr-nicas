"""Cliente asíncrono y explícito para la API v2 de 2Captcha."""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from typing import Any

import httpx

from .excepciones import ScrapingError


API_URL = "https://api.2captcha.com"


class CaptchaResolutionError(ScrapingError):
    """Error de configuración, creación o resolución de una tarea de captcha."""

    retryable = False


@dataclass(frozen=True)
class TurnstileSolution:
    """Resultado mínimo necesario para enviar un Turnstile al formulario destino."""

    token: str
    task_id: int
    cost: str | None = None


def _validar_respuesta(payload: dict[str, Any]) -> None:
    if payload.get("errorId", 0) != 0:
        raise CaptchaResolutionError(
            f"2Captcha rechazó la tarea: {payload.get('errorCode', 'ERROR_DESCONOCIDO')}"
        )


async def resolver_turnstile_proxyless(
    *,
    website_url: str,
    website_key: str,
    action: str | None = None,
    cdata: str | None = None,
    pagedata: str | None = None,
    api_key: str | None = None,
    client: httpx.AsyncClient | None = None,
    poll_interval_seconds: float = 5,
    timeout_seconds: float = 180,
) -> TurnstileSolution:
    """Resuelve un Turnstile con createTask/getTaskResult de API v2.

    No registra claves ni tokens. Los parámetros adicionales sólo se envían cuando
    el widget los expone; son necesarios para un Cloudflare Challenge.
    """
    client_key = api_key or os.getenv("API_KEY_2CAPTCHA")
    if not client_key:
        raise CaptchaResolutionError("Falta la variable de entorno API_KEY_2CAPTCHA.")
    if not website_url or not website_key:
        raise CaptchaResolutionError("Turnstile requiere website_url y website_key.")

    task: dict[str, str] = {
        "type": "TurnstileTaskProxyless",
        "websiteURL": website_url,
        "websiteKey": website_key,
    }
    if action:
        task["action"] = action
    if cdata:
        task["data"] = cdata
    if pagedata:
        task["pagedata"] = pagedata

    owns_client = client is None
    if owns_client:
        client = httpx.AsyncClient(timeout=30)

    try:
        created = await client.post(f"{API_URL}/createTask", json={"clientKey": client_key, "task": task})
        created.raise_for_status()
        created_payload = created.json()
        _validar_respuesta(created_payload)
        task_id = created_payload.get("taskId")
        if not isinstance(task_id, int):
            raise CaptchaResolutionError("2Captcha no devolvió un taskId válido.")

        elapsed = 0.0
        while elapsed < timeout_seconds:
            await asyncio.sleep(poll_interval_seconds)
            elapsed += poll_interval_seconds
            polled = await client.post(
                f"{API_URL}/getTaskResult", json={"clientKey": client_key, "taskId": task_id}
            )
            polled.raise_for_status()
            result = polled.json()
            _validar_respuesta(result)
            if result.get("status") == "processing":
                continue
            if result.get("status") != "ready":
                raise CaptchaResolutionError("2Captcha devolvió un estado de tarea no reconocido.")
            token = result.get("solution", {}).get("token")
            if not token:
                raise CaptchaResolutionError("2Captcha devolvió una tarea lista sin token.")
            return TurnstileSolution(token=token, task_id=task_id, cost=result.get("cost"))

        raise CaptchaResolutionError("Se agotó el tiempo esperando la resolución de Turnstile.")
    except httpx.HTTPError as error:
        raise CaptchaResolutionError("No fue posible comunicarse con la API de 2Captcha.") from error
    finally:
        if owns_client:
            await client.aclose()
