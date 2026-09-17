# CARFE: Automatización Robótica de Procesos (RPA) para el Control de Acuses de Recibo de Facturas Electrónicas

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

Este repositorio contiene el código fuente desarrollado como parte de la investigación de tesis de maestría: **"Automatización Robótica de Procesos (RPA) para el Control de Acuses de Recibo de Facturas Electrónicas (CARFE) por parte de los profesionales contables en Colombia"**.

**Autor:** Juan Carlos Rincón Vargas (Contador Público, juan310592@outlook.com)

---

## 📖 Contexto Académico e Investigación

La digitalización tributaria en Colombia, impulsada por la Ley 2155 de 2021, estableció la obligatoriedad de los Acuses de Recibo de Factura Electrónica como requisito indispensable para la procedencia de costos y deducciones fiscales. Esto transformó la dinámica del profesional contable, quien ahora enfrenta procesos manuales, repetitivos y vulnerables al error humano.

Para mitigar el riesgo fiscal y optimizar la carga operativa, esta investigación desarrolló un RPA estructurado en código capaz de navegar autónomamente en el portal de la Dirección de Impuestos y Aduanas Nacionales (DIAN). El sistema resuelve bloqueos técnicos críticos, como la gestión de captchas y la extracción masiva de información, demostrando en pruebas piloto una optimización drástica del tiempo invertido frente a métodos tradicionales y proponiendo un cambio de paradigma en el rol del contador moderno.

## ⚙️ Arquitectura Técnica de la Solución RPA

El proyecto implementa una API RESTful que actúa como motor central del RPA, orquestando tareas asíncronas de *web scraping* y procesamiento masivo de datos.

### Tecnologías Core

- **Backend & API:** Construida con **FastAPI** (Python), proporcionando una interfaz moderna, rápida y autodocumentada.
- **Motor RPA (Scraping):** Integración con **Playwright** para la automatización robusta de navegadores, permitiendo la interacción asíncrona con el portal de la DIAN sin intervención humana.
- **Resolución de Captchas:** Implementación de servicios de terceros (`2Captcha`) para evadir bloqueos de seguridad anti-bot (Turnstile) del portal gubernamental.
- **Concurrencia:** Uso extensivo de **`asyncio`** para manejar múltiples consultas paralelas, lo que reduce exponencialmente los tiempos de procesamiento en lotes masivos.
- **Procesamiento de Datos:** Uso de `Pandas` y `Openpyxl` para la lectura y generación de reportes estructurados en formato Excel (`.xlsx`).

## 🚀 Funcionalidades Principales

1. **Consulta Individual y Masiva de CUFE:** Verificación automatizada del estado, acuses de recibo y eventos asociados al Código Único de Factura Electrónica directamente en los servidores de la DIAN.
2. **Procesamiento por Lotes:** Capacidad para cargar archivos `.xlsx` con miles de registros y procesarlos de forma paralela.
3. **Exportación de Resultados:** Generación automática de matrices de control fiscal en Excel con el estado real y eventos (ej. RADIAN) de cada documento verificado.

## Puesta en funcionamiento

### Requisitos

- Python 3 con `venv` disponible.
- Google Chrome instalado. La API usa un Chrome normal y aislado para conservar
  la sesión validada por Cloudflare; no usa el perfil personal del navegador.
- Una cuenta de 2Captcha y una clave API con saldo, para los casos en que DIAN
  solicite resolver el widget Turnstile.
- Acceso a `https://catalogo-vpfe.dian.gov.co` desde el equipo que ejecuta la
  aplicación.

> El uso del portal DIAN y de 2Captcha debe estar autorizado y respetar los
> términos de ambos servicios. La clave de 2Captcha puede generar cargos: no la
> publiques, no la subas a Git ni la incluyas en logs.

### 1. Preparar el proyecto

Desde la raíz del repositorio:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
```

Para verificar la instalación:

```bash
.venv/bin/python -m unittest discover -v
.venv/bin/python -m pip check
```

Playwright se conecta al Chrome ya instalado mediante CDP; por ello no es
necesario descargar un navegador de Playwright para la operación habitual.

### 2. Configurar las variables de entorno

Copia el ejemplo y edita solamente los valores necesarios:

```bash
cp .env.example .env
```

Contenido de referencia de `.env`:

```env
# Obligatoria cuando la página no tenga un token Turnstile válido.
API_KEY_2CAPTCHA="REEMPLAZAR_POR_TU_CLAVE"

# Consultas DIAN simultáneas. Mantener 1 reduce bloqueos de Cloudflare/DIAN.
MAX_WORKERS=1

# Cantidad total de intentos por CUFE, incluido el primer intento.
DIAN_MAX_ATTEMPTS=3

# Espera inicial entre intentos en segundos. Se duplica en cada reintento:
# con 3 intentos y valor 2, las esperas son 2 s y 4 s.
DIAN_RETRY_BASE_DELAY_SECONDS=2

# Perfil exclusivo de CARFE; no apuntar al perfil personal de Chrome.
CARFE_BROWSER_PROFILE_DIR=.carfe-browser-profile

# CDP queda limitado al equipo local. No exponer este puerto en la red.
CARFE_CHROME_CDP_PORT=9223
CARFE_CHROME_CDP_URL=http://127.0.0.1:9223

# Ruta de Chrome en Linux. Ajustar únicamente si Chrome está instalado en otra ruta.
CARFE_CHROME_EXECUTABLE=/opt/google/chrome/chrome
```

Variables y comportamiento:

| Variable | Requerida | Función |
| --- | --- | --- |
| `API_KEY_2CAPTCHA` | Sí, si no existe token Turnstile válido | Clave privada usada para crear una tarea de resolución. Los errores definitivos de 2Captcha no se reintentan para evitar cargos duplicados. |
| `MAX_WORKERS` | Recomendada | Máximo de consultas concurrentes. El valor predeterminado es `3`, pero para DIAN se recomienda empezar con `1`. |
| `DIAN_MAX_ATTEMPTS` | Recomendada | Máximo total de intentos por CUFE, incluido el primero. El predeterminado es `3`; también cubre un HTTP 403 transitorio. |
| `DIAN_RETRY_BASE_DELAY_SECONDS` | Recomendada | Pausa inicial para backoff exponencial. El predeterminado es `2`; puede ser `0` sólo para pruebas locales. |
| `CARFE_BROWSER_PROFILE_DIR` | Recomendada | Directorio del perfil aislado que guarda la sesión de CARFE. El predeterminado es `.carfe-browser-profile`; no usar un perfil personal. |
| `CARFE_CHROME_CDP_PORT` y `CARFE_CHROME_CDP_URL` | Recomendada | Puerto y URL local mediante los que la API se conecta al Chrome aislado. Los predeterminados usan `9223` y deben coincidir si se modifican. |
| `CARFE_CHROME_EXECUTABLE` | Recomendada | Ejecutable de Google Chrome usado para abrir el perfil aislado. El predeterminado corresponde a la instalación habitual de Linux. |

Si se cambia alguna variable, detén e inicia de nuevo la API. Si cambias el
puerto CDP, cierra el Chrome CARFE anterior antes de volver a inicializarlo.

### 3. Inicializar Chrome para DIAN

En una primera terminal, con el entorno configurado, ejecuta:

```bash
.venv/bin/python -m paquetes.inicializar_perfil_dian
```

Se abrirá un Chrome independiente en la página de consulta DIAN. Completa
manualmente cualquier verificación de Cloudflare que aparezca y, cuando veas el
formulario de búsqueda, vuelve a la terminal y presiona `Enter`.

Mantén esa ventana de Chrome abierta mientras uses la API. El proceso no copia
cookies del navegador personal ni cierra el Chrome CARFE al finalizar una
consulta. Si la API indica que Chrome no está abierto, repite este paso.

### 4. Iniciar la API

En una segunda terminal, desde la raíz del proyecto:

```bash
.venv/bin/python run_app.py
```

La documentación interactiva estará en [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).
El script actual escucha en el puerto 8000; no lo publiques directamente a
Internet ni expongas el puerto CDP 9223. Para un entorno de red se requiere una
capa de autenticación, TLS y restricción de acceso antes de exponer la API.

### 5. Formato del archivo de entrada

El endpoint de carga acepta únicamente archivos `.xlsx`. Lee la primera hoja y
requiere exactamente estas columnas:

```text
CUFE/CUDE
NIT Emisor
Tipo de documento
Forma de Pago
Grupo
```

Solo se enviarán a DIAN las filas con estas condiciones:

- `Tipo de documento`: `Factura electrónica` o `Factura electrónica de contingencia`.
- `Forma de Pago`: `2` o `3`.
- `Grupo`: `Recibido`.
- `CUFE/CUDE` no vacío y `NIT Emisor` compuesto únicamente por dígitos. El NIT se
  consulta sin puntos, comas ni dígito de verificación.

No se admiten todavía archivos `.xls`, `.csv`, `.ods`, ni una hoja que solo
contenga CUFE y NIT.

### 6. Flujo de consulta mediante Swagger

1. Abre `http://127.0.0.1:8000/docs`.
2. En `POST /ingreso-archivo-cufes/`, selecciona el `.xlsx` y pulsa **Execute**.
3. Copia el `session_id` de la respuesta. Es temporal y vence tras una hora.
4. En `POST /consulta-masiva-cufes/`, pulsa **Try it out**, ingresa el valor en
   el encabezado `session-id` y ejecuta la solicitud.
5. Descarga `resultado_consultas_cufes.xlsx` de la respuesta.

El resultado incluye el CUFE, tipo y datos del documento, eventos y el enlace
de consulta. Si un CUFE termina como `error_procesamiento`, la columna
`Eventos` conserva el mensaje técnico para su revisión.

También puedes consultar una factura individual con:

```text
GET /cufe-individual/{cufe}?nit={nit_emisor}
```

Ejemplo de llamada local:

```bash
curl "http://127.0.0.1:8000/cufe-individual/CUFE_AQUI?nit=900123456"
```

### Diagnóstico sin consultas ni captcha

Para comprobar que el Chrome aislado sigue accesible y que la página carga, sin
enviar CUFEs ni crear tareas de captcha:

```bash
.venv/bin/python -m paquetes.diagnostico_dian
```

## Problemas frecuentes

| Situación | Acción recomendada |
| --- | --- |
| `Chrome CARFE no está abierto` | Ejecuta `python -m paquetes.inicializar_perfil_dian`, completa Cloudflare y deja Chrome abierto. |
| HTTP 403 en una consulta | Se reintenta según `DIAN_MAX_ATTEMPTS`. Si persiste, vuelve a validar Cloudflare y reduce `MAX_WORKERS` a `1`. |
| Error de 2Captcha | Revisa saldo, clave y el mensaje devuelto. No se reintenta automáticamente un error definitivo del proveedor. |
| Archivo rechazado | Confirma extensión `.xlsx`, primera hoja y nombres exactos de las cinco columnas requeridas. |
| No hay documentos para procesar | Revisa los cuatro filtros definidos en la sección de formato de entrada. |
