import os
import asyncio
import time
import re
import random
from bs4 import BeautifulSoup
import pandas as pd
import html
from tqdm import tqdm
from .excepciones import ScrapingError, CufeNotFoundError, FileProcessingError
from twocaptcha import TwoCaptcha
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import logging

# Obtener un logger para este módulo
logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------------
# Decorador para reintentos con backoff exponencial (versión async)
# --------------------------------------------------------------------------------
def backoff_delay(attempt, base_delay=2):
    """
    Calcula el tiempo de espera según la fórmula:
    delay = base_delay * 2^(attempt).
    """
    return base_delay * (2 ** attempt)

def retry(max_retries=5, base_delay=2):
    """
    Decorador para reintentar la ejecución de una función asíncrona ante excepciones,
    usando backoff exponencial en cada reintento.
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            ex = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    ex = e
                    if attempt < max_retries - 1:
                        delay = backoff_delay(attempt, base_delay)
                        logger.warning(f"Error en {func.__name__}: {e}. Reintentando en {delay} seg (intento {attempt + 1}/{max_retries})...")
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"Máximo de reintentos alcanzado para {func.__name__}. Último error: {e}")
            raise ScrapingError(f"Falló la operación {func.__name__} después de {max_retries} intentos. Último error: {ex}")
        return wrapper
    return decorator

# --------------------------------------------------------------------------------
# Funciones para solicitudes y scraping de contenido HTML
# --------------------------------------------------------------------------------

@retry(max_retries=5, base_delay=2)
async def obtener_pagina_con_cufe(cufe, browser_instance=None):
    """
    Resuelve un captcha Turnstile, ingresa un CUFE y obtiene el HTML resultante usando Playwright.
    Si se proporciona `browser_instance`, la utiliza; de lo contrario, crea una nueva.
    """
    if not cufe:
        raise ValueError("El CUFE no puede estar vacío.")

    solver = TwoCaptcha(os.getenv("API_KEY_2CAPTCHA", ""), defaultTimeout=180)

    async def _perform_scraping(browser):
        page = await browser.new_page()
        try:
            await page.goto('https://catalogo-vpfe.dian.gov.co/User/SearchDocument', timeout=60000)
            
            # Espera a que la página principal y sus recursos terminen de cargar.
            await page.wait_for_load_state('load', timeout=30000)

            await page.wait_for_selector('.cf-turnstile', timeout=30000)
            
            resultado = solver.turnstile(
                sitekey='0x4AAAAAAAg1WuNb-OnOa76z',
                url='https://catalogo-vpfe.dian.gov.co/User/SearchDocument'
            )
            token = resultado['code']

            await page.evaluate(f'document.querySelector("[name=\'cf-turnstile-response\']").value="{token}";')
            await page.fill('#DocumentKey', cufe)
            
            # Pequeña pausa antes de hacer clic para asegurar que el JS de la página se haya estabilizado.
            await asyncio.sleep(1)

            # Hacemos clic y le damos 60 segundos para que la navegación se complete.
            await page.click("xpath=//button[contains(text(),'Buscar')]", timeout=60000)

            # Esperar a que aparezca el contenedor de resultados o un mensaje de error de captcha
            await page.wait_for_selector(
                'div.container-md, span.field-validation-error', 
                timeout=60000
            )

            # Comprobar si apareció el mensaje de error
            error_message_element = await page.query_selector('span.field-validation-error')
            if error_message_element:
                error_message = await error_message_element.inner_text()
                if "Falta Token de validación de captcha" in error_message:
                    logger.warning(f"Fallo de validación de captcha para CUFE {cufe}. Reintentando...")
                    raise ScrapingError(f"Fallo de validación de captcha para CUFE {cufe}")

            return await page.content()
        except PlaywrightTimeoutError as e:
            logger.error(f"Error de scraping (timeout) para CUFE {cufe}: {e}")
            
            # Guardar HTML y captura de pantalla para depuración
            debug_dir = "debug_logs"
            os.makedirs(debug_dir, exist_ok=True)
            
            # Usar un timestamp para nombres de archivo únicos
            timestamp = int(time.time())
            screenshot_path = os.path.join(debug_dir, f"timeout_screenshot_{cufe[:10]}_{timestamp}.png")
            html_path = os.path.join(debug_dir, f"timeout_html_{cufe[:10]}_{timestamp}.txt")
            
            try:
                await page.screenshot(path=screenshot_path)
                logger.info(f"Captura de pantalla guardada en: {screenshot_path}")
                
                content = await page.content()
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(content)
                logger.info(f"HTML guardado en: {html_path}")
            except Exception as save_e:
                logger.error(f"No se pudo guardar la información de depuración: {save_e}")

            raise ScrapingError(f"No se pudo obtener la página para el CUFE {cufe} debido a un timeout.")
        finally:
            await page.close()

    if browser_instance:
        return await _perform_scraping(browser_instance)
    else:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                return await _perform_scraping(browser)
            finally:
                await browser.close()


def consultar_html(contenido_html, cufe):
    """
    Procesa el contenido HTML para extraer la información relevante.
    """
    url_base = f"https://catalogo-vpfe.dian.gov.co/document/searchqr?documentKey={cufe}"

    if not contenido_html or "404 - Documento no encontrado" in contenido_html:
        raise CufeNotFoundError(cufe)

    soup = BeautifulSoup(contenido_html, "html.parser")

    event_codes = ["030", "031", "032", "033", "034"]
    extracted_event_codes = [code for code in event_codes if soup.find("td", string=code)]
    if not extracted_event_codes:
        extracted_event_codes = ["sin_eventos"]

    match_tipo = re.search(r'<span class="tipo-doc"><b>([^<]+)</b></span>', contenido_html)
    tipo_documento = html.unescape(match_tipo.group(1)) if match_tipo else None

    match_serie = re.search(r"Serie:\s*([\w\s]+)<br>", contenido_html)
    serie = match_serie.group(1) if match_serie else None

    match_folio = re.search(r"Folio:\s*([\d]+)<br>", contenido_html)
    folio = match_folio.group(1) if match_folio else None

    match_fecha = re.search(r"Fecha de emisión de la factura Electrónica:\s*([\d\-]+)<br>", contenido_html)
    fecha_emision = match_fecha.group(1) if match_fecha else None

    emisor_nit_element = soup.find(string=re.compile(r"NIT:"))
    emisor_nit = emisor_nit_element.split(":")[1].strip() if emisor_nit_element else None
    emisor_nombre_element = emisor_nit_element.find_next(string=re.compile(r"Nombre:")) if emisor_nit_element else None
    emisor_nombre = emisor_nombre_element.split(":")[1].strip() if emisor_nombre_element else None

    receptor_nit_element = soup.find(string="DATOS DEL RECEPTOR")
    if receptor_nit_element:
        receptor_nit_element = receptor_nit_element.find_next(string=re.compile(r"NIT:"))
    receptor_nit = receptor_nit_element.split(":")[1].strip() if receptor_nit_element else None
    receptor_nombre_element = receptor_nit_element.find_next(string=re.compile(r"Nombre:")) if receptor_nit_element else None
    receptor_nombre = receptor_nombre_element.split(":")[1].strip() if receptor_nombre_element else None

    iva_element = soup.find(string=re.compile(r"IVA:"))
    iva_str = iva_element.split(":")[1].strip().replace("$", "").replace(",", "") if iva_element else "0.0"
    try:
        iva = float(iva_str)
    except ValueError:
        iva = 0.0

    total_element = soup.find(string=re.compile(r"Total:"))
    total_str = total_element.split(":")[1].strip().replace("$", "").replace(",", "") if total_element else "0.0"
    try:
        total = float(total_str)
    except ValueError:
        total = 0.0

    subtotal = total - iva if total >= iva else 0.0

    data = {
        "Cufe": cufe,
        "Tipo de Documento": tipo_documento,
        "Serie": serie,
        "Folio": folio,
        "Fecha de Emisión": fecha_emision,
        "NIT Emisor": emisor_nit,
        "Nombre Emisor": emisor_nombre,
        "NIT Receptor": receptor_nit,
        "Nombre Receptor": receptor_nombre,
        "Subtotal": subtotal,
        "IVA": iva,
        "Total": total,
        "Eventos": "-".join(extracted_event_codes),
        "Link": url_base,
    }
    return data

async def consulta_individual(cufe):
    """
    Consulta un CUFE individualmente.
    """
    # Llama a la función refactorizada sin pasar una instancia de browser.
    # La función se encargará de crear y destruir la instancia por sí misma.
    contenido_html = await obtener_pagina_con_cufe(cufe)
    resultado = consultar_html(contenido_html, cufe)
    return resultado

async def consulta_cufe_paralelo(cufes, max_trabajadores: int = None):
    """
    Consulta múltiples CUFEs en paralelo de forma eficiente, reutilizando una
    única instancia de navegador y limitando la concurrencia.
    El número de trabajadores se toma de la variable de entorno MAX_WORKERS.
    """
    if max_trabajadores is None:
        max_trabajadores = int(os.getenv("MAX_WORKERS", 3))
    
    resultados = []
    sem = asyncio.Semaphore(max_trabajadores)

    async def _consultar_y_procesar(browser, cufe):
        # Pausa aleatoria para "humanizar" el tráfico y evitar bloqueos
        await asyncio.sleep(random.uniform(0.5, 3.0))
        async with sem:
            try:
                # Pasamos la instancia compartida del navegador
                contenido_html = await obtener_pagina_con_cufe(cufe, browser_instance=browser)
                return consultar_html(contenido_html, cufe)
            except CufeNotFoundError:
                return {"Cufe": cufe, "Tipo de Documento": "cufe_no_encontrado"}
            except Exception as e:
                logger.error(f"Error procesando el CUFE {cufe}: {e}")
                return {"Cufe": cufe, "Tipo de Documento": "error_procesamiento", "Eventos": str(e)}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            tasks = [_consultar_y_procesar(browser, cufe) for cufe in cufes]
            for future in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Consultando CUFEs"):
                resultado = await future
                resultados.append(resultado)
        finally:
            await browser.close()
            
    return resultados

def tipo_archivo(nombre_archivo):
    """
    Lee un archivo y devuelve su contenido como una lista de líneas.
    """
    try:
        with open(nombre_archivo, "r", encoding="utf-8") as archivo:
            contenido = archivo.read()
        lista_lineas = [line.strip() for line in contenido.split("\n") if line.strip()]
        return lista_lineas, None
    except Exception as e:
        raise FileProcessingError(nombre_archivo, e)
