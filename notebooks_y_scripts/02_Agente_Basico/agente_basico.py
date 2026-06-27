"""
Agente IA Básico SIN MEMORIA
Solo modelo + prompt - No recuerda conversaciones anteriores

Este es un ejemplo de lo que pasa cuando un agente NO tiene memoria:
- Cada mensaje es independiente
- No recuerda lo que dijiste antes
- No puede mantener contexto de la conversación
"""

import os
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate

# ===========================================
# Se asegura que se carguen las variables de entorno desde el archivo .env
# ===========================================
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

# ===========================================
# Se carga la clave de la API de OpenAI desde las variables de entorno
# ===========================================
openai_key = os.getenv("OPENAI_API_KEY")
if openai_key:
    print("OPENAI_API_KEY encontrada. ¡Todo listo para usar la API de OpenAI!")
else:
    raise ValueError("OPENAI_API_KEY no encontrada. Verifica tu archivo .env")

# ============================================
# 1. CONFIGURACIÓN DEL MODELO
# ============================================
chat = init_chat_model(
    "gpt-4.1",
    model_provider="openai",
    temperature=0.7, # 0 a 1, no es configurable para modelos razonadores.
    api_key=openai_key,
)

# ============================================
# 2. PROMPT SIMPLE (Sin placeholder de historial)
# ============================================
prompt = ChatPromptTemplate.from_messages([
    ("system", 
     """Eres un asistente de IA útil y amigable llamado DataBot. 
    Responde las preguntas del usuario de manera clara y concisa.
    Responde siempre en español."""),
    ("human", "{input}")
])

# ============================================
# 3. CREAR LA CHAIN (Solo prompt | modelo), LCEL
# ============================================
chain = prompt | chat

# ============================================
# 4. FUNCIÓN SIMPLE SIN MEMORIA
# ============================================
def chat_con_agente(mensaje_usuario: str) -> str:
    """
    Envía un mensaje al agente.
    ⚠️ NO mantiene historial - cada mensaje es independiente.
    """
    respuesta = chain.invoke({"input": mensaje_usuario})
    return respuesta.content

# ============================================
# 5. LOOP DE CONVERSACIÓN
# ============================================
def main():
    print("=" * 50)
    print("🤖 DataBot - Agente SIN MEMORIA")
    print("=" * 50)
    print("⚠️  Este agente NO recuerda mensajes anteriores")
    print("Escribe 'salir' para terminar.\n")
    
    print("*" * 60)
    print("💬 Comienza a chatear con DataBot:")
    
    while True:
        usuario = input("Usuario: ").strip()
        print(f"\n Persona: {usuario}\n")
        
        if usuario.lower() in ['salir', 'exit', 'quit']:
            print("\n¡Hasta luego! 👋")
            break
        
        if not usuario:
            continue
        
        respuesta = chat_con_agente(usuario)        
        print(f"🤖 DataBot: {respuesta}\n")

# ============================================
# MAIN
# ============================================
if __name__ == "__main__":
    main()