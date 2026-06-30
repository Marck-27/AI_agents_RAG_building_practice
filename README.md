# AI Engineering Practice

Proyecto educativo de construcción progresiva de agentes de IA con LangChain y OpenAI. Cada módulo introduce un nuevo concepto: primero se explora en un notebook `.ipynb` y luego se consolida en un script `.py` reutilizable que puede ser invocado desde los orquestadores.

---

## Estructura del proyecto

```
AI_Engineering_for_Devs/
├── notebooks_y_scripts/
│   ├── 01_embeddings_similitud_semantica/   # Conceptos de embeddings y similitud
│   ├── 02_Agente_Basico/                    # Agente sin memoria
│   ├── 03_Agente_Basico_con_Memoria_Historica/  # Agente con historial en PostgreSQL
│   ├── 04_vectorizacion_docs_for_RAG/       # Carga de documentos a Supabase (vectores)
│   ├── 05_Agente_con_RAG_basico/            # Agente con base de conocimiento (RAG)
│   ├── 06_Agente_con_RAG_multi_tools/       # Agente completo: RAG + Internet + Fecha/Hora
│   ├── main.py                              # Orquestador interactivo (CLI)
│   └── main_chatwoot_ia_off.py              # Webhook para integración con Chatwoot
├── tools/
│   ├── Base_de_conocimiento.py              # Tool: búsqueda RAG en Supabase
│   ├── Busqueda_internet.py                 # Tool: búsqueda web con Tavily
│   └── Hora_y_fecha.py                      # Tool: fecha y hora por zona horaria
├── pyproject.toml
└── uv.lock
```

---

## Módulos y progresión

### 01 — Embeddings y similitud semántica
**Archivo:** `01_embeddings_similitud_semantica/embeddings.ipynb`

Introduce los conceptos de embeddings de texto y cálculo de similitud coseno. No requiere servicios externos más allá de la API de OpenAI.

---

### 02 — Agente Básico (sin memoria)
**Archivos:** `agente_basico.ipynb` / `agente_basico.py`

Agente mínimo: modelo + prompt. Demuestra la ausencia de contexto entre turnos — cada mensaje es independiente.

- Modelo: `gpt-4.1`
- Sin persistencia ni herramientas

---

### 03 — Agente con Memoria Histórica
**Archivos:** `agente_basico_conversation_history.ipynb` / `agente_basico_conversation_history.py`

Agente que persiste el historial de conversación en PostgreSQL (Supabase). Permite retomar sesiones por `session_id` (UUID).

- Modelo: `gpt-4.1`
- Persistencia: PostgreSQL vía `langchain-postgres`
- La tabla de historial se crea automáticamente al iniciar si no existe

---

### 04 — Vectorización de documentos para RAG
**Archivos:** `vectorizacion_doc_hacia_supabase.ipynb` / `snippet_para_Supabase.sql`

Carga un PDF (`Base_de_Conocimientos/`) y lo convierte en embeddings que se almacenan en Supabase con `pgvector`. Este paso es **prerequisito** para los módulos 05 y 06.

- Modelo de embeddings: `text-embedding-ada-002`
- Almacenamiento: tabla `documentos_vectorizados` en Supabase
- El SQL para crear la tabla y la función de búsqueda está en `snippet_para_Supabase.sql`

---

### 05 — Agente con RAG básico
**Archivos:** `agente_basico_hc_base_de_conocimiento.ipynb` / `agente_basico_hc_base_de_conocimiento.py`

Agente que usa la base de conocimiento como herramienta (tool). El LLM decide cuándo invocarla. Combina RAG + historial persistente en PostgreSQL.

- Tool: `buscar_informacion` (búsqueda por similitud coseno en Supabase)
- Persistencia: PostgreSQL

---

### 06 — Agente Completo (RAG + Internet + Fecha/Hora)
**Archivos:** `agente_basico_hc_bc_toolexterna.ipynb` / `agente_basico_hc_bc_toolexterna.py`

Agente con todas las capacidades: base de conocimiento, búsqueda web en tiempo real y consulta de fecha/hora por zona horaria. Es el agente producción que consume `main_chatwoot_ia_off.py`.

- Tools: `buscar_informacion`, `buscar_internet`, `obtener_fecha_hora`
- Persistencia: PostgreSQL
- Modelo: `gpt-4.1`

---

## Orquestadores

### `main.py` — CLI interactivo

Menú en terminal para seleccionar y ejecutar cualquier agente:

```bash
uv run python notebooks_y_scripts/main.py
```

```
A → Agente Básico (sin memoria)
B → Agente con Memoria Histórica (PostgreSQL)
C → Agente con RAG básico (Memoria + RAG)
D → Agente Completo (Memoria + RAG + Internet + Fecha/Hora)
0 → Salir
```

### `main_chatwoot_ia_off.py` — Webhook FastAPI para Chatwoot

Servidor HTTP que recibe eventos de Chatwoot y responde automáticamente usando el Agente Completo (módulo 06). Incluye:

- Handoff a humano al detectar palabras clave (`humano`, `asesor`, etc.)
- Etiqueta `ia-off` para desactivar la IA en conversaciones específicas
- Endpoints: `POST /webhook`, `POST /test`, `GET /health`

```bash
uv run python notebooks_y_scripts/main_chatwoot_ia_off.py
```

---

## Herramientas (`/tools`)

| Archivo | Tool exportada | Descripción |
|---|---|---|
| `Base_de_conocimiento.py` | `buscar_informacion` | Busca por similitud coseno en la tabla de embeddings de Supabase |
| `Busqueda_internet.py` | `buscar_internet` | Búsqueda web en tiempo real con Tavily (hasta 5 resultados) |
| `Hora_y_fecha.py` | `obtener_fecha_hora` | Fecha y hora actual por zona horaria IANA (sin APIs externas) |

---

## Requisitos

### Entorno — UV

El proyecto usa [uv](https://docs.astral.sh/uv/) como gestor de entornos y dependencias.

```bash
# Instalar uv (si no está instalado)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Crear entorno e instalar dependencias
uv sync

# Registrar el kernel en Jupyter (para los notebooks)
uv run python -m ipykernel install --user --name ai-engineering-for-devs
```

Python mínimo requerido: **3.11**

---

### Dependencias principales

| Librería | Uso |
|---|---|
| `langchain`, `langchain-openai` | Framework de agentes y modelos |
| `langchain-community` | Integraciones adicionales |
| `langchain-postgres` | Historial de chat en PostgreSQL |
| `langchain-tavily` | Tool de búsqueda web |
| `langchain-text-splitters` | Fragmentación de documentos para RAG |
| `supabase` | Cliente Python para Supabase |
| `psycopg` | Conexión directa a PostgreSQL |
| `pypdf` | Lectura de PDFs para vectorización |
| `fastapi` + `uvicorn` | Servidor webhook para Chatwoot |
| `python-dotenv` | Gestión de variables de entorno |
| `scikit-learn`, `numpy` | Cálculo de similitud coseno |

---

### Variables de entorno — `.env`

Crear un archivo `.env` en la raíz del proyecto con las siguientes variables:

```env
# ─── OpenAI ───────────────────────────────────────────
OPENAI_API_KEY=sk-...

# ─── Supabase / PostgreSQL ────────────────────────────
# Credenciales para conexión directa a PostgreSQL (sesión 03, 05, 06)
DB_USER=postgres.xxxxxxxxxxxx
DB_PASSWORD=tu_password
DB_HOST=aws-0-us-east-1.pooler.supabase.com
DB_PORT=5432
DB_NAME=postgres

# Credenciales del cliente Supabase (sesión 04, 05, 06 — RAG)
SUPABASE_URL=https://xxxxxxxxxxxx.supabase.co
SUPABASE_SECRET_KEY=eyJ...

# Nombre de la tabla con embeddings (creada en el paso 04)
TABLE_EMBEDDINGS=documentos_vectorizados

# Nombre de la tabla de historial de chat (se crea automáticamente)
TBL_NAME_CHAT_USER_BOT=chat_history

# ─── Tavily (búsqueda web) ────────────────────────────
TAVILY_API_KEY=tvly-...

# ─── Zona horaria del agente (opcional, default: America/Lima) ───
AGENT_TIMEZONE=America/Lima

# ─── Chatwoot (solo para main_chatwoot_ia_off.py) ─────
CHATWOOT_BASE_URL=https://app.chatwoot.com
CHATWOOT_ACCOUNT_ID=123
CHATWOOT_API_ACCESS_TOKEN=tu_token
CHATWOOT_BOT_LABEL=atiende-ia
```

---

### Servicios externos requeridos

#### 1. OpenAI
- API key con acceso a `gpt-4.1` y `text-embedding-ada-002`
- Obtener en: https://platform.openai.com/api-keys

#### 2. Supabase (PostgreSQL + pgvector)
Supabase provee tanto la base de datos PostgreSQL para el historial como el almacén vectorial para RAG.

**Pasos de configuración:**

a. Crear proyecto en https://supabase.com

b. Habilitar la extensión `pgvector` y crear la tabla de embeddings ejecutando el SQL de `snippet_para_Supabase.sql` (disponible en las carpetas `04_`, `05_` y `06_`):

```sql
-- Habilitar pgvector
create extension if not exists vector;

-- Tabla de embeddings
create table if not exists documentos_vectorizados (
  id uuid primary key default gen_random_uuid(),
  content text,
  metadata jsonb,
  embedding vector(1536)
);

-- Función de búsqueda por similitud
create or replace function similar_documentos_vectorizados(
  query_embedding vector(1536),
  match_count int,
  filter jsonb
) returns table (id uuid, content text, metadata jsonb, similarity float)
language plpgsql as $$
begin
  return query
  select id, content, metadata,
    1 - (documentos_vectorizados.embedding <=> query_embedding) as similarity
  from documentos_vectorizados
  where metadata @> filter
  order by documentos_vectorizados.embedding <=> query_embedding
  limit match_count;
end;
$$;
```

c. Las credenciales de conexión directa (Transaction Pooler) están en: **Project Settings → Database → Connection string**

d. La `SUPABASE_SECRET_KEY` está en: **Project Settings → API → service_role secret**

> La tabla de historial de chat (`TBL_NAME_CHAT_USER_BOT`) **se crea automáticamente** al ejecutar los agentes 03, 05 o 06. No requiere SQL manual.

#### 3. Tavily (búsqueda web)
- Requerido solo para el módulo 06 y el webhook de Chatwoot
- Plan gratuito disponible en: https://tavily.com
- Asignar la API key a `TAVILY_API_KEY` en `.env`

#### 4. Chatwoot (solo para el webhook)
- Solo requerido para `main_chatwoot_ia_off.py`
- Instancia propia (self-hosted) o en la nube: https://www.chatwoot.com
- Configurar un webhook apuntando a la URL pública del servidor (ej. con [ngrok](https://ngrok.com) en desarrollo)
- El webhook debe recibir el evento `message_created`

---

## Orden de ejecución recomendado

```
01 → Explorar embeddings (solo OpenAI API key)
02 → Agente básico sin memoria (solo OpenAI API key)
03 → Agente con memoria (OpenAI + Supabase/PostgreSQL)
04 → Vectorizar documentos (OpenAI + Supabase con pgvector)
05 → Agente con RAG (OpenAI + Supabase)
06 → Agente completo (OpenAI + Supabase + Tavily)
```

Una vez completados los módulos, usar `main.py` para ejecutar cualquier agente desde un menú interactivo, o `main_chatwoot_ia_off.py` para desplegar el agente como servicio webhook.
