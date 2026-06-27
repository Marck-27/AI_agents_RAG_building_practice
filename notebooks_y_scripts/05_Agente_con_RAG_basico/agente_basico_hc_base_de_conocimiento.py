"""
Agente IA con Tools + Histórico de Conversación
- RAG como Tool: El LLM decide cuándo buscar en la base de conocimiento
- Histórico: Guarda conversaciones en PostgreSQL
- Extensible: Fácil agregar más Tools
"""

import os
import uuid
from urllib.parse import quote_plus

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_postgres import PostgresChatMessageHistory
import psycopg

# ===========================================
# Se asegura que se carguen las variables de entorno desde el archivo .env
# ===========================================
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

# ===========================================
# Se agrega el path raiz para poder importar los modulos de la carpeta "/tools"
# ===========================================
import sys
from pathlib import Path

# Path del archivo actual
#PATH_FILE = Path.cwd() # usar con "notebooks.ipynb"
PATH_FILE = Path(__file__).parent # usar con "scripts.py"
print(f"Path del archivo actual: {PATH_FILE}")

# Path raiz del projecto
PATH_ROOT = str(PATH_FILE.parent.parent)
print(f"Path raiz del proyecto: {PATH_ROOT}")

# Se agrega el Path raiz para cargar módulos correctamente
sys.path.insert(0, PATH_ROOT)

# Importar tools desde la carpeta "tools/"
from tools.Base_de_conocimiento import buscar_informacion


# ============================================
# Carga de variables de entorno para la conexión a PostgreSQL
# ============================================
DB_USER     = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST     = os.getenv("DB_HOST")
DB_PORT     = os.getenv("DB_PORT", "5432")
DB_NAME     = os.getenv("DB_NAME", "postgres")

if not all([DB_USER, DB_PASSWORD, DB_HOST]):
    raise ValueError(
        "❌ Faltan variables de base de datos en .env\n"
        "Requeridas: DB_USER, DB_PASSWORD, DB_HOST\n"
        "Opcionales: DB_PORT (default: 5432), DB_NAME (default: postgres)"
    )

# quote_plus maneja caracteres especiales en la contraseña (@ # $ etc.)
DATABASE_URL = f"postgresql://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

print(f"🔌 Conectando como: {DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

# ============================================
# CREAR TABLA DE HISTORIAL de texto en PostgreSQL
# (Se usará para almacenar el historial de chat entre el usuario y el bot)
# ============================================

# Nombre de la tabla en supabase para almacenar el historial textual de chat User-Bot
TBL_NAME_CHAT_USER_BOT = os.getenv("TBL_NAME_CHAT_USER_BOT")

def crear_tabla_historial(table_name: str = TBL_NAME_CHAT_USER_BOT):
    """Crea la tabla de historial en PostgreSQL si no existe."""
    try:
        sync_connection = psycopg.connect(DATABASE_URL)

        # Se crea tabla (si no existe) con la estructura necesaria 
        # para almacenar el historial de chat (creada por "PostgresChatMessageHistory")
        PostgresChatMessageHistory.create_tables(sync_connection, table_name)
        
        sync_connection.close()

        print(f"✅ Tabla '{table_name}' lista en PostgreSQL")
    except Exception as e:
        print(f"⚠️ Nota sobre tabla: {e}")

crear_tabla_historial()

# ============================================
# FUNCIÓN QUE CARGA EL HISTÓRICO DE CONVERSACIÓN
# ============================================
def get_session_history(session_id: str, table_name: str = TBL_NAME_CHAT_USER_BOT) -> PostgresChatMessageHistory:
    sync_connection = psycopg.connect(DATABASE_URL)
    return PostgresChatMessageHistory(
        table_name,
        session_id,
        sync_connection=sync_connection
    )

# ============================================
# LISTA DE TOOLS DISPONIBLES
# ============================================
# Agregar aquí todas las tools que quieras usar
tools = [
    buscar_informacion, # <-- se deberá referenciar en el "system_prompt"
]
# En la tool "buscar_informacion" se realiza la búsqueda de información en la base de datos vectorial,
# la cual contiene información en embeddings creados en el notebook de vectorización de la base de conocimiento.

# ============================================
# CONFIGURACIÓN DEL MODELO CON TOOLS
# ============================================
chat = init_chat_model(
    "gpt-4.1", 
    temperature=0.4
)

chat_con_tools = chat.bind_tools(tools)

# ============================================
# PROMPT DEL AGENTE en donde de le indica cuando usar las tools y cuando no
# ============================================
system_prompt = """Eres DataBot, un asistente de IA de DATAPATH.

Tu objetivo es ayudar a los usuarios respondiendo sus preguntas.

INSTRUCCIONES:
- Para preguntas sobre DATAPATH (programas, cursos, precios, docentes), USA la herramienta "buscar_informacion".
- Para saludos, agradecimientos o conversación general, responde directamente SIN usar herramientas.
- Recuerdas toda la conversación gracias a tu memoria persistente.
- Responde siempre en español de manera clara y amigable.

EJEMPLOS de cuándo NO usar herramientas (no se hacen preguntas sobre DATAPATH):
- "Hola" → Responde con un saludo
- "Gracias" → Responde amablemente
- "¿Cómo estás?" → Responde conversacionalmente

EJEMPLOS de cuándo SÍ usar la herramienta "buscar_informacion":
- "¿Qué cursos tienen?" → Usa la Tool "buscar_informacion"
- "¿Cuánto cuesta el programa de IA?" → Usa la Tool "buscar_informacion"
- "¿Quiénes son los docentes?" → Usa la Tool "buscar_informacion" """

# ============================================
# 7. FUNCIÓN DE CHAT CON AGENTE + TOOLS
# ============================================
def chat_con_agente(mensaje_usuario: str, session_id: str) -> str:
    """
    Ejecuta el agente con tools y memoria.
    El agente decide si usar herramientas o responder directamente.
    """
    # ***********************************************************
    # Obtener historial
    # con esto el agente puede recordar la conversaciones previas con un mismo usuario
    history = get_session_history(session_id)
    mensajes_previos = history.messages
    
    # Construir mensajes para el modelo
    messages = [{"role": "system", "content": system_prompt}]
    
    # Agregar historial
    for msg in mensajes_previos:
        if isinstance(msg, HumanMessage):
            messages.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            messages.append({"role": "assistant", "content": msg.content})
    
    # Agregar mensaje actual
    messages.append({"role": "user", "content": mensaje_usuario})
    
    # ***********************************************************
    # Invocar modelo con tools
    # con esto, el agente decide si usar herramientas o responder directamente
    response = chat_con_tools.invoke(messages)
    
    # Procesar tool calls si existen
    if response.tool_calls:
        # Ejecutar cada tool
        tool_results = []
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            # Buscar y ejecutar la tool
            for t in tools:
                if t.name == tool_name:
                    result = t.invoke(tool_args)
                    tool_results.append({
                        "tool_call_id": tool_call["id"],
                        "result": result
                    })
                    break
        
        # Agregar respuesta del modelo con tool calls y resultados
        messages.append(response)
        for tr in tool_results:
            messages.append(ToolMessage(
                content=tr["result"],
                tool_call_id=tr["tool_call_id"]
            ))
        
        # Segunda llamada para obtener respuesta final
        final_response = chat_con_tools.invoke(messages)
        respuesta_final = final_response.content
    else:
        # Sin tool calls, respuesta directa
        respuesta_final = response.content
    
    # Guardar en historial
    history.add_user_message(mensaje_usuario)
    history.add_ai_message(respuesta_final)
    
    return respuesta_final

# ============================================
# 8. LOOP DE CONVERSACIÓN
# ============================================
def main():
    print("=" * 60)
    print("🤖 DataBot - Agente con TOOLS + MEMORIA PERSISTENTE")
    print("=" * 60)
    print("🔧 Tools disponibles:")
    for t in tools:
        print(f"   - {t.name}")
    print("💾 Historial: PostgreSQL")
    
    # Menú de sesión
    print("\nOpciones de sesión:")
    print("  1. Nueva conversación")
    print("  2. Continuar sesión existente (pegar UUID)")
    
    opcion = input("\nElige (1/2): ").strip()
    
    if opcion == "2":
        session_id = input("Pega el UUID de la sesión: ").strip()
        try:
            uuid.UUID(session_id)
        except ValueError:
            print("⚠️ UUID inválido. Creando nueva sesión...")
            session_id = str(uuid.uuid4())
    else:
        session_id = str(uuid.uuid4())
    
    print(f"\n📝 Session ID: {session_id}")
    print("   (Guarda este ID para continuar después)")
    print("✅ El agente DECIDE cuándo buscar en la base de conocimiento")
    print("Escribe 'salir' para volver al menú.\n")
    
    print("*" * 60)
    print("💬 Comienza a chatear con DataBot:")
    while True:
        usuario = input("Tú: ").strip()
        print(f"💬 Usuario: {usuario}")
        
        if usuario.lower() in ['salir', 'exit', 'quit']:
            print(f"\n💾 Tu sesión está guardada.")
            print(f"   UUID: {session_id}")
            print("👋 ¡Hasta luego!")
            break
        
        if not usuario:
            continue
        
        try:
            respuesta = chat_con_agente(usuario, session_id)
            print(f"🤖 DataBot: {respuesta}\n")
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


# ============================================
# MAIN
# ============================================
if __name__ == "__main__":
    main()