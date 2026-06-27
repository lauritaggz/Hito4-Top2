# Asistente RAG de Soporte Técnico

Proyecto mínimo de **Retrieval-Augmented Generation (RAG)** para responder preguntas técnicas usando documentos locales sobre Docker, Linux, Git y procedimientos de soporte.

**Caso seleccionado:** Asistente de Soporte Técnico.

## Problema abordado

Los equipos de soporte necesitan consultar manuales y guías dispersas para resolver incidencias. Este asistente indexa documentos locales en una base vectorial y genera respuestas contextualizadas con un modelo de lenguaje local, citando las fuentes utilizadas.

## Arquitectura RAG

```
Usuario → Pregunta → Embedding → ChromaDB → Recuperación de contexto → Qwen3/Ollama → Respuesta + Fuentes
```

1. El usuario formula una pregunta en Streamlit.
2. La pregunta se convierte en un vector (embedding) con `nomic-embed-text`.
3. ChromaDB recupera los 4 fragmentos más similares.
4. Esos fragmentos se envían como contexto a `qwen3:4b` en Ollama.
5. El modelo genera una respuesta breve con fuentes.

## Tecnologías utilizadas

| Componente | Tecnología |
|------------|------------|
| Lenguaje | Python |
| Interfaz | Streamlit |
| Base vectorial | ChromaDB |
| LLM local | Ollama (`qwen3:4b`) |
| Embeddings | Ollama (`nomic-embed-text`) |
| Documentos | Markdown, TXT, PDF (`pypdf`) |

## Instalación

```bash
cd rag-soporte-tecnico
pip install -r requirements.txt
```

### Preparar modelos en Ollama

```bash
ollama pull nomic-embed-text
```

El modelo `qwen3:4b` debe estar ya disponible. Verifíquelo con:

```bash
ollama list
```

## Ejecución

```bash
python ingest.py
streamlit run app.py
```

La ingesta lee los documentos de `data/docs/`, genera chunks, calcula embeddings y los guarda en `chroma_db/`. La aplicación Streamlit permite hacer preguntas sobre el contenido indexado.

## Ejecución con Docker

Ollama **no** corre dentro del contenedor. Debe estar instalado y activo en el computador anfitrión (Windows con Docker Desktop / WSL2, Linux o macOS). El contenedor Python se conecta a Ollama mediante `http://host.docker.internal:11434`.

Los volúmenes montados permiten:

- **`data/docs`**: cambiar documentos sin reconstruir la imagen.
- **`chroma_db`**: persistir la base vectorial entre ejecuciones.

**Orden recomendado:** primero ingesta, luego la aplicación.

### 1. Verificar que Ollama esté corriendo en el computador

```bash
ollama list
```

### 2. Verificar que existan los modelos

```bash
ollama list
```

Deben aparecer:

- `qwen3:4b`
- `nomic-embed-text`

Si falta nomic:

```bash
ollama pull nomic-embed-text
```

### 3. Crear archivo de entorno Docker

```bash
cp .env.docker.example .env.docker
```

En Windows también puede duplicar manualmente el archivo `.env.docker.example` y renombrarlo a `.env.docker`.

### 4. Construir la imagen

```bash
docker compose build
```

### 5. Ejecutar la ingesta documental

```bash
docker compose --profile ingest run --rm rag-ingest
```

### 6. Ejecutar la aplicación

```bash
docker compose up rag-app
```

### 7. Abrir en navegador

```
http://localhost:8501
```

### 8. Apagar

```bash
docker compose down
```

### Linux nativo (sin Docker Desktop)

En Linux, Docker Compose crea una red virtual distinta y el firewall del sistema suele **bloquear** conexiones desde el contenedor hacia Ollama en el host, aunque uses `host.docker.internal`. Por eso puede aparecer un *timeout* aunque `ollama list` funcione en la terminal.

Usa el archivo adicional `docker-compose.linux.yml`, que ejecuta los contenedores con `network_mode: host` y conecta a Ollama en `http://127.0.0.1:11434`:

```bash
docker compose -f docker-compose.yml -f docker-compose.linux.yml build
docker compose -f docker-compose.yml -f docker-compose.linux.yml --profile ingest run --rm rag-ingest
docker compose -f docker-compose.yml -f docker-compose.linux.yml up rag-app
```

En **Windows con Docker Desktop** o **macOS** no hace falta este override; basta con `docker-compose.yml` y `.env.docker` con `host.docker.internal`.

## Justificación del chunking

Usamos **chunk size 700** y **overlap 100** porque permite fragmentos suficientemente pequeños para recuperar información específica, manteniendo continuidad entre fragmentos relacionados.

## Conceptos clave

### Embeddings

Un embedding es una representación numérica de un texto. Textos con significado similar producen vectores cercanos en el espacio vectorial, lo que permite comparar preguntas con fragmentos de documentos.

### Búsqueda semántica

En lugar de buscar palabras exactas, la búsqueda semántica compara el significado de la pregunta con el de los chunks almacenados, recuperando los más relevantes aunque no compartan las mismas palabras.

### ChromaDB

ChromaDB es una base de datos vectorial persistente. Almacena embeddings, textos y metadatos (archivo fuente, número de chunk, página) para consultas rápidas por similitud.

### Generación de la respuesta

El LLM recibe la pregunta junto con los fragmentos recuperados e instrucciones para responder solo con ese contexto. Si la información no está presente, debe indicarlo explícitamente.

### Preguntas fuera del contexto

Si ningún fragmento contiene la respuesta, el sistema responde:

> No encontré información suficiente en los documentos disponibles para responder con seguridad.

## Ventajas de RAG

- Respuestas basadas en documentación propia, no en conocimiento genérico del modelo.
- Trazabilidad mediante fuentes citadas.
- Ejecución 100 % local, sin APIs externas ni costos por token.
- Fácil actualización: basta reindexar documentos con `python ingest.py`.

## Limitaciones de RAG

- La calidad depende de los documentos indexados y del chunking.
- Puede recuperar fragmentos parcialmente relevantes.
- Modelos pequeños pueden simplificar o malinterpretar el contexto.
- No sustituye un sistema de tickets ni acceso a infraestructura real.

## Preguntas sugeridas para la demo

1. ¿Cómo crear una imagen Docker?
2. ¿Cómo puedo actualizar un repositorio Git y verificar si tengo cambios pendientes?
3. ¿Cómo puedo ver los procesos activos en Linux?
4. ¿Qué datos debo incluir al abrir un ticket de soporte?
5. ¿Cuál es el sueldo promedio de un ingeniero en Corea? *(sin respuesta documental)*

## Estructura del proyecto

```
rag-soporte-tecnico/
├── app.py              # Interfaz Streamlit
├── ingest.py           # Ingesta e indexación
├── rag.py              # Recuperación y generación
├── config.py           # Configuración centralizada
├── ollama_utils.py     # Verificación de Ollama y modelos
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── data/docs/          # Documentos fuente
└── chroma_db/          # Base vectorial persistente
```
