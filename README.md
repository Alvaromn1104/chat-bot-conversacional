# Conversational E-commerce Backend

Backend de un asistente conversacional orientado a e-commerce, capaz de gestionar catálogo, carrito y proceso de compra mediante lenguaje natural.

El proyecto está diseñado con un enfoque **práctico y mantenible**, combinando reglas deterministas, parsers de intención basados en heurísticas y un flujo conversacional controlado mediante un grafo de estados.

---

## 🚀 Instalación y ejecución

### Requisitos

- Python 3.10 o superior
- `pip`

### Instalación de dependencias

pip install -r requirements.txt

### Variables de entorno (opcional)

LLM_ROUTER_ENABLED=false
OPENAI_API_KEY=your_api_key_here
Por defecto, el proyecto funciona sin LLM.

### Ejecución

uvicorn app.main:app --reload
El servicio quedará disponible en: http://localhost:8000

## Demo interactiva (Gradio)

El repositorio incluye un frontend ligero en `gradio_chat.py` como **demo opcional** del sistema conversacional.

Este archivo permite interactuar con el motor (LangGraph + reglas + LLM opcional) sin necesidad de configurar un frontend adicional.

Para ejecutarlo:

python gradio_chat.py

## ✨ Funcionalidades Principales

### 🛍️ Gestión de Catálogo e Inteligencia
- **Recomendaciones avanzadas**: Filtra productos por aroma, rango de precio o público objetivo (hombre, mujer, unisex).
- **Auto-asistencia**: Si preguntas _"¿Qué puedes hacer?"_, el bot detalla todas sus capacidades y comandos disponibles.

### 🛒 Carrito de Compra
- Añadir / quitar productos por **ID o nombre**.
- Modificación de cantidades.
- Resumen detallado del total acumulado.

### 💳 Checkout con Formulario Dinámico
Proceso de compra guiado mediante un flujo de estado que incluye:
- Recolección de datos de envío y contacto.
- Validaciones integradas:
  - Formato de email
  - Códigos postales
  - Campos obligatorios
- Confirmación final antes de procesar el pedido.


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

---


