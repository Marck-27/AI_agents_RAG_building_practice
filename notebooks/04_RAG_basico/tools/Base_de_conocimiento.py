"""
Tool: Base de Conocimiento (RAG con Supabase)
Permite buscar información en la base de conocimientos de DATAPATH.
"""

import os
import json
import numpy as np
from langchain_openai import OpenAIEmbeddings
from langchain_core.tools import tool
from supabase import create_client

#from dotenv import load_dotenv, find_dotenv
#load_dotenv(find_dotenv())

# ============================================
# CARGA DE CREDENCIALES PARA CONEXIÓN A TABLA DE EMBEDDINGS EN SUPABASE
# ============================================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

# Nombre de la tabla en Supabase donde se almacenan los embeddings
TABLE_EMBEDDINGS = os.getenv("TABLE_EMBEDDINGS")

if not all([SUPABASE_URL, SUPABASE_SECRET_KEY, TABLE_EMBEDDINGS]):
    raise ValueError(
        "❌ Faltan variables de Supabase en .env\n"
        "Requeridas: SUPABASE_URL, SUPABASE_SECRET_KEY, TABLE_EMBEDDINGS"
    )

# Crear cliente de Supabase
supabase_client = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)


# ============================================
# FUNCIONES INTERNAS
# ============================================
def calcular_similitud_coseno(vec1, vec2):
    """Calcula la similitud de coseno entre dos vectores."""
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    return 1 - np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

# ============================================
# MODELO DE EMBEDDINGS
# (Debe ser el mismo modelo usado para generar los embeddings de los documentos en la base de datos)
# ============================================
embedding_model = OpenAIEmbeddings(
    model='text-embedding-ada-002' # Modelo de embeddings
)

#============================================
# SE CREA LÓGICA QUE SE USARÁ COMO TOOL PARA BUSCAR INFORMACIÓN EN LA BASE DE CONOCIMIENTO
#============================================
def buscar_en_base_conocimiento_interno(query: str, TABLE_EMBEDDINGS: str = TABLE_EMBEDDINGS, top_k: int = 5) -> str:
    """
    Función interna de búsqueda RAG.

    Convierte la consulta del usuario en un embedding, recupera todos los documentos
    de la tabla de embeddings en Supabase, calcula la similitud de coseno entre el
    embedding de la consulta y el embedding de cada documento, y retorna un
    resumen con los top_k documentos más relevantes.

    Args:
        query: Consulta de búsqueda
        TABLE_EMBEDDINGS: Nombre de la tabla de embeddings
        top_k: Número de documentos a retornar

    Returns:
        str: Información encontrada formateada
    """
    try:
        # Convierte la consulta del usuario al embedding correspondiente
        query_vector = embedding_model.embed_query(query)
        
        # Se cargan todos los campos de la tabla de embeddings
        result = supabase_client.table(TABLE_EMBEDDINGS).select('*').execute()
        
        if not result.data:
            return "No hay documentos (embeddings) en la base de conocimientos."
        
        # Calcular similitud para cada documento (vector-embedding) y almacenar resultados
        documentos_con_score = []
        for doc in result.data:

            # Se verifica que el documento tenga valores en el campo "embedding"
            if doc.get('embedding'):

                # Se carga embedding
                vector_i = doc['embedding']
                if isinstance(vector_i, str):
                    vector_i = json.loads(vector_i)
                
                # Se convierte embedding a lista de floats
                vector_i = [float(x) for x in vector_i]
                
                # Se calcula similitud de coseno entre el embedding de la consulta y el embedding actual del documento
                score = calcular_similitud_coseno(query_vector, vector_i)
                
                # Se almacena el contenido del documento y su score
                documentos_con_score.append({
                    'content': doc.get('content', ''),
                    'score': score
                })
        
        # Ordenar por similitud y obtener los top_k documentos más relevantes
        documentos_con_score.sort(key=lambda x: x['score'])
        top_docs = documentos_con_score[:top_k]
        

        if not top_docs:
            return "No encontré información relevante."
        
        # Se construye el contexto con los documentos más relevantes
        # Se muestra la relevancia como porcentaje (1 - score) para que el agente pueda ver qué tan relevante es cada documento
        contexto = "Información encontrada:\n\n"
        for i, doc in enumerate(top_docs, 1):
            similitud = 1 - doc['score']
            contexto += f"[{i}] (Relevancia: {similitud:.0%})\n{doc['content']}\n\n"
        
        return contexto
        
    except Exception as e:
        return f"Error al buscar: {str(e)}"


# ============================================
# SE EXPORTA LA TOOL PARA USO EN EL AGENTE
# ============================================
@tool
def buscar_informacion(consulta: str, TABLE_EMBEDDINGS: str = TABLE_EMBEDDINGS) -> str:
    """
    Busca información sobre DATAPATH en la base de conocimientos.
    Usa esta herramienta cuando el usuario pregunte sobre:
    - Programas de DATAPATH
    - Cursos y contenidos
    - Docentes e instructores
    - Precios y modalidades
    - Cualquier información relacionada con DATAPATH
    
    Args:
        consulta: La pregunta o tema a buscar
        TABLE_EMBEDDINGS: Nombre de la tabla de embeddings
    """
    print(f"   🔍 Buscando: '{consulta}'")
    resultado = buscar_en_base_conocimiento_interno(consulta, TABLE_EMBEDDINGS)
    return resultado
