# Conversational E-commerce Backend

Backend de un asistente conversacional orientado a e-commerce, capaz de gestionar catálogo, carrito y proceso de compra mediante lenguaje natural.

El proyecto está diseñado con un enfoque **práctico y mantenible**, combinando reglas deterministas, parsers de intención basados en heurísticas y un flujo conversacional controlado mediante un grafo de estados.

---

## 🚀 Instalación y ejecución

### Requisitos

- Python 3.11 o superior
- Gestor de dependencias `uv` (recomendado)

### 📦 Instalación de dependencias

Este proyecto utiliza el estándar moderno de Python basado en `pyproject.toml`.

Las dependencias están declaradas en dicho archivo y bloqueadas mediante `uv.lock`,
lo que garantiza un entorno reproducible.

#### Opción recomendada (con `uv`)

`pip install uv`
`uv sync`

#### Opción alternativa (sin `uv`)

`pip install -e`

### Variables de entorno (opcional)

LLM_ROUTER_ENABLED=false
OPENAI_API_KEY=your_api_key_here
Por defecto, el proyecto funciona sin LLM.

### Ejecución

uvicorn app.main:app --reload
El servicio quedará disponible en: http://localhost:8000

## 📟 Demo interactiva (Gradio)

El repositorio incluye un **frontend interactivo basado en Gradio** (`gradio_chat.py`) que sirve como **demo funcional del asistente conversacional**.

Este frontend permite:
- Probar el flujo completo de conversación en tiempo real.
- Ver cómo el sistema interpreta lenguaje natural y ejecuta acciones sobre catálogo, carrito y checkout.
- Evaluar el comportamiento del motor conversacional sin necesidad de integrar un frontend externo.

La demo conecta directamente con el backend (**LangGraph + reglas deterministas + LLM opcional**), por lo que refleja fielmente el comportamiento real del sistema.

> 💡 **Nota sobre el frontend**  
> El frontend se ha implementado deliberadamente en **un único archivo (`gradio_chat.py`)** para simplificar su ejecución, revisión y uso.  
> De este modo, se evita la creación de un repositorio adicional y se mantiene el foco en el **núcleo del proyecto: la lógica y el comportamiento del chatbot conversacional**.

### Ejecución de la demo

python gradio_chat.py

## ✨ Funcionalidades Principales

### 🛍️ Catálogo y Recomendaciones Inteligentes
- Consulta del catálogo completo y detalle de productos por **ID o nombre**.
- **Recomendaciones personalizadas** basadas en:
  - Familia olfativa (cítrico, amaderado, floral, etc.)
  - Rango de precios
  - Público objetivo (hombre, mujer, unisex)
- Soporte de lenguaje natural en **español e inglés**.
- Detección automática de idioma y adaptación de respuestas.

### 🛒 Gestión Avanzada de Carrito
- Añadir y eliminar productos por **ID, nombre o contexto conversacional**.
- Soporte de **comandos múltiples en una sola frase**  
  (ej.: _"añádeme 2 del 315 y 1 del 317"_).
- Modificación de cantidades y ajustes posteriores  
  (ej.: _"mejor deja solo uno"_).
- Resolución de ambigüedades con preguntas de aclaración cuando es necesario.
- Cálculo y visualización del total en tiempo real.

### 🔄 Flujo Conversacional Robusto
- Motor determinista basado en **reglas priorizadas** y **estado conversacional**.
- Manejo de:
  - Contexto activo del producto
  - Confirmaciones
  - Clarificaciones
  - Operaciones pendientes
- Fallbacks controlados para entradas fuera de alcance (_out of scope_).

### 💳 Checkout Guiado
- Proceso de compra estructurado mediante un **flujo de estados**.
- Recolección de datos de envío mediante formulario dinámico.
- Validaciones integradas:
  - Campos obligatorios
  - Formato numérico (CP, teléfono)
- Confirmación explícita antes de finalizar la compra.


## 🧠 Uso de LLM (opcional)

El sistema puede utilizar un LLM de OpenAI para clasificación de intención y extracción de slots. Este comportamiento es opcional y está desactivado por defecto.

### Variables relevantes:

Fragmento de código

LLM_ROUTER_ENABLED=true
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=gpt-4.1-mini
LLM_MIN_CONFIDENCE=0.3

## 🧪 Tests

El proyecto incluye tests automatizados que cubren los flujos principales de catálogo, carrito y checkout.
pytest -q

## 💬 Ejemplos de uso

### Consulta de Capacidades

Usuario: ¿Qué puedes hacer?

Bot: Puedo ayudarte a buscar perfumes por aroma o precio, gestionar tu carrito y tramitar tu compra. Prueba a decirme "Busca perfumes cítricos".

### Recomendaciones

Usuario: Búscame un perfume para mujer de menos de 80€

Bot: He encontrado estas opciones para ti: ...

### Checkout (Validación)

Usuario: Finalizar compra

---

## 📁 Demo adicional (Notebook y registros de conversación)

Como complemento, el proyecto incluye material demostrativo para facilitar la evaluación del comportamiento conversacional sin necesidad de ejecutar el sistema completo.

### 📓 Notebook / Script de demostración

En la carpeta `docs/` se incluye un **notebook o script de demo** que muestra:

- Ejecución de conversaciones completas paso a paso.
- Ejemplos de parsing determinista (carrito, recomendaciones).
- Flujo de estados del asistente sin necesidad de frontend.

Este material permite revisar rápidamente la lógica del sistema y entender cómo se combinan reglas, estado y (opcionalmente) LLM.

### 💬 Registro de conversaciones

También se incluye un **archivo de registro de conversación** con ejemplos reales de interacción usuario–bot, donde se pueden observar:

- Resolución de ambigüedades.
- Operaciones múltiples de carrito en un solo mensaje.
- Cambio de idioma durante la conversación.
- Flujos completos de recomendación y checkout.

---

## 🌍 Soporte multilenguaje (ES / EN)

El asistente está diseñado para operar de forma natural tanto en **español como en inglés**.

### Características clave:

- Detección automática del idioma del usuario.
- Respuestas coherentes en el idioma detectado.
- Cambio dinámico de idioma durante la conversación si el usuario lo hace.
- Copys centralizados por idioma para facilitar mantenimiento y extensión.

Ejemplo:

> Usuario inicia en español → el bot responde en español  
> Usuario cambia a inglés → el bot adapta automáticamente sus respuestas

---

## 🧩 Diseño orientado a producción

Aunque se trata de una prueba técnica, el backend está estructurado con criterios cercanos a un entorno real:

- Separación clara entre:
  - reglas de routing
  - nodos de conversación
  - servicios de dominio
  - capa de UX / copy
- Flujos deterministas priorizados antes de recurrir a LLM.
- Estados limpiados explícitamente para evitar efectos colaterales entre turnos.
- Arquitectura fácilmente extensible a nuevos intents, idiomas o canales (chat, API, UI).

📄 Para un análisis más detallado del diseño y del flujo conversacional basado en LangGraph, puede consultarse el documento  
**`docs/Arquitectura_Chatbot_Langraph.pdf`**, donde se describe la arquitectura del bot en mayor profundidad.


---


