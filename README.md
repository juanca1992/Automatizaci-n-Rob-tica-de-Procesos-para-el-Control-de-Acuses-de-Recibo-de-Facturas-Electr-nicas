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

## 🛠️ Instalación y Despliegue

### Requisitos Previos

- Python 3.8 o superior.
- Clave API válida del servicio `2Captcha`.

### Configuración del Entorno

1. Clona este repositorio:
   ```bash
   git clone https://github.com/tu-usuario/CAFRE.git
   cd CAFRE
   ```

2. Crea un archivo `.env` en el directorio raíz con la siguiente configuración:
   ```env
   # Clave de API para el servicio de resolución de captchas
   API_KEY_2CAPTCHA="TU_API_KEY_AQUI"

   # Número de hilos/consultas paralelas (ajustar según CPU y límites de la DIAN)
   MAX_WORKERS=6
   ```

3. Instala las dependencias del proyecto:
   ```bash
   pip install -r requirements.txt
   ```

4. Instala los binarios de los navegadores para Playwright:
   ```bash
   playwright install
   ```

### Ejecución de la API

Inicia el servidor local ejecutando:

```bash
python run_app.py
```

El servidor del RPA se iniciará localmente. Puedes acceder a la interfaz gráfica de la API y su documentación interactiva (Swagger UI) navegando a:
`http://localhost:8000/docs`

## 📊 Impacto y Conclusiones

La implementación de este RPA (CARFE) demuestra la viabilidad técnica de reemplazar procesos operativos manuales en contabilidad mediante herramientas programáticas avanzadas. Los resultados confirman que la automatización no solo elimina el riesgo de digitación y fallos de validación humana frente a obligaciones fiscales, sino que permite al contador público redirigir su esfuerzo cognitivo hacia el análisis financiero, el planeamiento tributario y la toma de decisiones gerenciales de alto valor.
