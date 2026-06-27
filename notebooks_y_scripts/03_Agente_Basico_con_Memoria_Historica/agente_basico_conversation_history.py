"""
Agente IA con Histórico de Conversación en PostgreSQL
Mantiene memoria persistente de las conversaciones

Este agente:
- Guarda cada mensaje en PostgreSQL
- Recuerda conversaciones anteriores
- Puede retomar conversaciones por session_id
"""

import os

# uuid módulo para generar identificadores únicos universales (UUIDs)
import uuid

from urllib.parse import quote_plus
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_postgres import PostgresChatMessageHistory
import psycopg

# ===========================================
# Se asegura que se carguen las variables de entorno desde el archivo .env
# ===========================================
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

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
# Inicializa el modelo de chat con la configuración deseada
# ============================================
chat = init_chat_model(
    "gpt-4.1",
    temperature=0.1,
)

# ============================================
# Se inicializa el prompt de chat con el historial de conversación
# ============================================
prompt = ChatPromptTemplate.from_messages([
    ("system", """Eres un asistente de IA útil y amigable llamado DataBot.
Responde las preguntas del usuario de manera clara y concisa.
Puedes recordar conversaciones anteriores gracias a tu memoria persistente.
Responde siempre en español."""),
    MessagesPlaceholder(variable_name="history"),  # ← ② HISTORIAL SE INYECTA AQUÍ
    ("human", "{input}")
])

# ============================================
# Se crea cadena de ejecución que combina el prompt y el modelo de chat
# ============================================
chain = prompt | chat

# ============================================
# Función para obtener el historial de la sesión desde PostgreSQL
# ============================================
def get_session_history(session_id: str) -> PostgresChatMessageHistory:
    """
    ① HISTORIAL LEÍDO — llamada automáticamente por RunnableWithMessageHistory.
    Retorna un objeto que lee y escribe mensajes de la sesión desde PostgreSQL.
    """
    sync_connection = psycopg.connect(DATABASE_URL)
    return PostgresChatMessageHistory(
        TBL_NAME_CHAT_USER_BOT,                        # nombre de la tabla
        session_id,                      # UUID que identifica la conversación
        sync_connection=sync_connection  # conexión sincrónica a PostgreSQL
    )

# ===========================================
# Se crea un Runnable que combina la cadena de ejecución con el historial de conversación
#===========================================
chain_con_historial = RunnableWithMessageHistory(
    chain,                           # ③ cadena base: prompt | chat
    get_session_history,             # ① función que devuelve el historial por session_id
    input_messages_key="input",      # clave del mensaje del usuario en el dict de entrada
    history_messages_key="history",  # ② clave del MessagesPlaceholder en el prompt
)

# ============================================
# Función para enviar un mensaje al agente con historial persistente
# ============================================
def chat_con_agente(mensaje_usuario: str, session_id: str) -> str:
    """
    Envía un mensaje al agente con historial persistente.
    El session_id identifica la conversación en PostgreSQL.
    """
    respuesta = chain_con_historial.invoke(
        {"input": mensaje_usuario},
        config={"configurable": {"session_id": session_id}}  # ← identifica la sesión para cargar el historial de la conversación desde PostgreSQL
    )
    return respuesta.content

# ============================================
# Función principal para ejecutar el agente con historial de conversación
# ============================================
def main():
    print("=" * 60)
    print("🤖 DataBot - Agente CON MEMORIA PERSISTENTE (PostgreSQL)")
    print("=" * 60)

    print("\nOpciones de sesión:")
    print("  1. Nueva conversación")
    print("  2. Continuar sesión existente (pegar UUID)")

    opcion = input("\nElige (1/2): ").strip()

    if opcion == "2":
        session_id = input("\nPega el UUID de la sesión: ").strip()
        try:
            uuid.UUID(session_id)  # valida que sea un UUID real
        except ValueError:
            print("⚠️ UUID inválido. Creando nueva sesión...")
            session_id = str(uuid.uuid4())
    else:
        print("\nCreando nueva sesión...")
        session_id = str(uuid.uuid4())  # nueva sesión con UUID único

    print(f"\n📝 Session ID: {session_id}")
    print("   (Guarda este ID para continuar la conversación después)")
    print("✅ Este agente RECUERDA tus mensajes anteriores")
    print("Escribe 'salir' para terminar.\n")

    print("*" * 60)
    print("💬 Comienza a chatear con DataBot:")
    while True:

        usuario = input("Usuario: ").strip()
        print(f"\n💬 Usuario: {usuario}")

        if usuario.lower() in ["salir", "exit", "quit"]:
            print(f"\n💾 Tu sesión está guardada.")
            print(f"   UUID: {session_id}")
            print("👋 ¡Hasta luego!")
            break

        # Si el usuario no ingresa nada, se ignora y se solicita nuevamente
        if not usuario:
            print("⚠️ Por favor, ingresa un mensaje.")
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