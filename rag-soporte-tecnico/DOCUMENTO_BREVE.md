# Implementación de un Asistente RAG de Soporte Técnico

## 1. Descripción del problema abordado

En entornos de soporte técnico es frecuente que los usuarios y analistas de primera línea necesiten consultar documentación sobre herramientas como Docker, Linux o Git, además de procedimientos internos para abrir tickets y escalar incidencias. Esta información suele encontrarse en varios archivos dispersos, lo que dificulta obtener respuestas rápidas y consistentes.

Para abordar este problema se implementó un **Asistente RAG (Retrieval-Augmented Generation)** de Soporte Técnico. El sistema indexa documentos locales en una base vectorial, recupera los fragmentos más relevantes ante cada pregunta y utiliza un modelo de lenguaje local para generar una respuesta fundamentada en esa documentación, indicando además las fuentes consultadas.

El objetivo no es reemplazar un sistema de tickets completo, sino demostrar cómo la recuperación aumentada permite responder preguntas técnicas de forma controlada, trazable y ejecutándose íntegramente en el equipo del usuario.

## 2. Tecnologías utilizadas

| Tecnología | Función en el proyecto |
|------------|------------------------|
| **Python** | Lenguaje principal del backend y scripts de ingesta |
| **Streamlit** | Interfaz web sencilla para formular preguntas y ver resultados |
| **ChromaDB** | Almacenamiento persistente de embeddings y metadatos |
| **Ollama** | Servidor local para ejecutar el LLM y el modelo de embeddings |
| **qwen3:4b** | Modelo de lenguaje para generar respuestas |
| **nomic-embed-text** | Modelo de embeddings para representar textos como vectores |
| **pypdf** | Lectura de documentos PDF durante la ingesta |

No se utilizaron APIs externas, LangChain, Redis ni contenedores Docker para ejecutar la aplicación, con el fin de mantener la solución simple, comprensible y adecuada para una demostración académica.

## 3. Flujo de funcionamiento de la solución

El funcionamiento del asistente sigue el pipeline RAG clásico:

1. **Ingesta (`ingest.py`)**: Se leen archivos Markdown, TXT y PDF desde `data/docs/`. Cada documento se divide en fragmentos (chunks) de 700 caracteres con solapamiento de 100. Cada chunk se convierte en un embedding mediante Ollama y se almacena en ChromaDB junto con metadatos (archivo fuente, número de chunk y página si aplica).

2. **Consulta del usuario (`app.py`)**: El usuario escribe una pregunta en la interfaz Streamlit y pulsa «Preguntar».

3. **Recuperación (`rag.py`)**: La pregunta se transforma en embedding y ChromaDB devuelve los 4 chunks más similares semánticamente.

4. **Generación**: Los fragmentos recuperados se incluyen en un prompt junto con instrucciones para no inventar información. El modelo `qwen3:4b` genera una respuesta breve. Si el contexto no contiene la respuesta, el sistema indica que no hay información suficiente.

5. **Presentación**: Streamlit muestra la respuesta, las fuentes utilizadas y, en un panel expandible, los fragmentos recuperados para fines de demostración y transparencia.

## 4. Capturas de pantalla

[Insertar captura de la interfaz aquí]

*Descripción sugerida: pantalla principal con título, caja de pregunta, barra lateral con modelos configurados e instrucciones de ejecución.*

[Insertar captura de una respuesta con fuentes aquí]

*Descripción sugerida: respuesta a una pregunta sobre Git o Docker, mostrando la sección de fuentes y el expander de fragmentos recuperados.*

## 5. Dificultades encontradas

Durante el desarrollo se presentaron algunos retos habituales en proyectos RAG locales:

- **Dependencia de Ollama**: Si el servicio no está en ejecución, la ingesta y las consultas fallan. Se añadieron validaciones básicas para informar al usuario con mensajes claros.

- **Comportamiento del modelo qwen3**: Algunos modelos incluyen bloques de razonamiento interno en la salida. Fue necesario filtrar esas etiquetas antes de mostrar la respuesta final en la interfaz.

- **Chunking y recuperación**: Un tamaño de chunk inadecuado puede fragmentar información relacionada o recuperar textos poco relevantes. Se adoptó chunk size 700 y overlap 100 como equilibrio entre precisión y contexto.

- **Preguntas fuera del dominio**: El LLM podría intentar responder con conocimiento general. Las instrucciones del prompt y la detección de respuestas de «información insuficiente» ayudan a mantener el comportamiento esperado.

## 6. Reflexión sobre ventajas y limitaciones de RAG

**Ventajas:** RAG permite anclar las respuestas del modelo a documentación verificable, lo que mejora la confianza y la trazabilidad. Al ejecutarse de forma local, no expone datos a servicios externos y es adecuado para entornos con restricciones de privacidad. Actualizar el conocimiento del asistente consiste en añadir o modificar documentos y volver a ejecutar la ingesta.

**Limitaciones:** La calidad final depende tanto de los documentos como de la capacidad del modelo pequeño para sintetizar el contexto. RAG no garantiza respuestas correctas si los fragmentos recuperados son irrelevantes o incompletos. Tampoco reemplaza flujos operativos completos como la gestión de tickets, la escalación automática o el acceso a sistemas en producción.

En conclusión, RAG es una técnica útil y demostrable para asistentes de soporte acotados, siempre que se definan expectativas realistas sobre su alcance y se complemente con procesos humanos cuando el problema exceda la documentación disponible.
