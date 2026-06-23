# backend.py - CON RESTRICCIONES ÉTICAS ORIGINALES
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import chromadb
import chromadb.utils.embedding_functions as embedding_functions
import google.generativeai as genai
import os
import json
import re
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# CONFIGURACIÓN
# ==========================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    modelo_gemini = genai.GenerativeModel("gemini-2.5-flash-lite")
else:
    modelo_gemini = None
    print("⚠️ GEMINI_API_KEY no encontrada")

CHROMA_PATH = "chroma_db"
client = chromadb.PersistentClient(path=CHROMA_PATH)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConsultaRequest(BaseModel):
    pregunta: str

# ==========================================
# 🔒 RESTRICCIONES ÉTICAS - FILTRO DE SEGURIDAD
# ==========================================

# Palabras y frases que activan el filtro ético
PALABRAS_RESTRINGIDAS = [
    # Diagnóstico y tratamiento
    "diagnostic", "recet", "medicament", "fármac", "dosis", "tratamient",
    "cur", "san", "curación", "terapi", "pastill", "jarab", "inyección",
    "antibiótic", "analgésic", "prescrib", "indicar tratamiento",
    # Síntomas y enfermedades (cuando se pide diagnóstico)
    "síntoma de", "síntomas de", "signos de", "enfermedad",
    # Consultas médicas directas
    "qué tengo", "qué enfermedad", "qué medicamento", "qué pastilla",
    "cómo curar", "cómo sanar", "tratamiento para",
    # Sustitución profesional
    "sustituir al médico", "reemplazar al médico", "en lugar del médico",
]

# Patrón compilado para búsqueda rápida
PATRON_RESTRINGIDO = re.compile(
    r'\b(' + '|'.join(PALABRAS_RESTRINGIDAS) + r')\b',
    re.IGNORECASE | re.UNICODE
)

# Mensaje de respuesta ética
RESPUESTA_ETICA = """🔒 **CONSULTA NO PERMITIDA POR RAZONES ÉTICAS**

Este asistente es una **herramienta educativa** para estudiantes de ciencias de la salud. No está diseñado para:

❌ Diagnosticar enfermedades
❌ Recetar medicamentos
❌ Recomendar tratamientos
❌ Interpretar síntomas clínicos

📚 **Preguntas permitidas:**
- Definiciones de conceptos médicos
- Información de libros de texto
- Preguntas académicas para estudio
- Explicaciones de procedimientos generales

👨‍⚕️ **Si tienes síntomas reales, consulta a un médico profesional.**

Fuentes: No aplica (consulta bloqueada por razones éticas)."""

# ==========================================
# FUNCIÓN PARA EXPANDIR LA PREGUNTA
# ==========================================
def expandir_pregunta(pregunta: str) -> str:
    stopwords = [
        "qué", "es", "el", "la", "los", "las", "un", "una", "de", "del", 
        "al", "para", "por", "como", "cuál", "cuáles", "que", "se", "me", 
        "te", "le", "lo", "la", "las", "los", "con", "sin", "sobre", "entre",
        "hacia", "desde", "hasta", "durante", "mediante", "según", "contra",
        "ante", "bajo", "cabe", "con", "contra", "de", "desde", "en", "entre",
        "hacia", "hasta", "para", "por", "según", "sin", "sobre", "tras"
    ]
    palabras = pregunta.lower().split()
    palabras_clave = [p for p in palabras if p not in stopwords and len(p) > 3]
    return " ".join(palabras_clave) if palabras_clave else pregunta


# ==========================================
# FUNCIÓN PARA VERIFICAR PREGUNTAS CLÍNICAS
# ==========================================
def es_pregunta_clinica(pregunta: str) -> bool:
    """Detecta si la pregunta es de naturaleza clínica (síntomas, diagnóstico, tratamiento)"""
    # Palabras que indican pregunta clínica
    patron_clinico = re.compile(
        r'\b('
        r'síntoma|signo|dolor|fiebre|tos|mareo|náusea|vómito|'
        r'fatiga|debilidad|inflamación|hinchazón|sangrado|hemorragia|'
        r'fractura|quemadura|herida|lesión|'
        r'presión|frecuencia|ritmo|pulso|respiración|'
        r'me duele|tengo dolor|siento|padezco|sufro de'
        r')\b',
        re.IGNORECASE | re.UNICODE
    )
    return bool(patron_clinico.search(pregunta))


@app.get("/")
def root():
    return {"mensaje": "API de asistente médico funcionando"}

@app.post("/consultar")
async def consultar(request: ConsultaRequest):
    # ==========================================
    # 🔒 FILTRO ÉTICO - VERIFICAR PREGUNTAS RESTRINGIDAS
    # ==========================================
    if PATRON_RESTRINGIDO.search(request.pregunta):
        return {
            "respuesta": RESPUESTA_ETICA,
            "fuentes": "🚫 Consulta bloqueada por razones éticas.",
            "bloqueada": True
        }
    
    try:
        collection = client.get_collection("libros_medicos")
        
        pregunta_expandida = expandir_pregunta(request.pregunta)
        
        resultados = collection.query(
            query_texts=[pregunta_expandida],
            n_results=5
        )
        
        if not resultados["documents"] or not resultados["documents"][0]:
            return {
                "respuesta": "No se encontró información relevante en los libros para responder tu pregunta.",
                "fuentes": "No hay fuentes disponibles",
                "bloqueada": False
            }
        
        documentos = resultados["documents"][0]
        metadatos = resultados["metadatas"][0]
        contexto = "\n\n".join(documentos)
        
        # ==========================================
        # DETECTAR SI ES PREGUNTA CLÍNICA PARA REDIRIGIR
        # ==========================================
        es_clinica = es_pregunta_clinica(request.pregunta)
        
        # ==========================================
        # CONSTRUIR PROMPT CON ADVERTENCIA ÉTICA
        # ==========================================
        if es_clinica:
            advertencia = """
⚠️ **NOTA IMPORTANTE:** Esta pregunta parece ser de naturaleza clínica (síntomas o condiciones médicas). 
Este asistente es educativo y NO puede diagnosticar ni recomendar tratamientos. 
La información proporcionada es solo académica. Consulta siempre a un médico profesional.
"""
        else:
            advertencia = ""
        
        prompt = f"""Eres un asistente médico **educativo y académico** para estudiantes universitarios.

**INSTRUCCIONES IMPORTANTES:**
1. Responde SOLO con información del CONTEXTO proporcionado.
2. Tu respuesta debe ser EDUCATIVA y ACADÉMICA, nunca clínica.
3. NO diagnostiques, NO recetes, NO recomiendes tratamientos.
4. NO interpretes síntomas ni des opiniones médicas.
5. Si la pregunta es clínica, incluye una advertencia clara.
6. Si el contexto tiene información, responde de forma COMPLETA y DETALLADA.
7. Si NO hay información, di: "No hay información suficiente en los libros para responder esta pregunta."
8. NO inventes información.
9. Menciona las fuentes específicas (libro y página).

{advertencia}

**CONTEXTO (información de libros de texto):**
{contexto}

**PREGUNTA DEL USUARIO:** {request.pregunta}

**RESPUESTA EDUCATIVA:**"""
        
        if modelo_gemini:
            response = modelo_gemini.generate_content(prompt)
            respuesta = response.text
        else:
            respuesta = "⚠️ Gemini no está configurado. Revisa tu API key."
        
        # ==========================================
        # FORMATEAR FUENTES
        # ==========================================
        fuentes_texto = []
        for meta in metadatos:
            libro = meta.get("libro", "Desconocido")
            pagina = meta.get("pagina", "?")
            fuentes_texto.append(f"📖 {libro} - Página {pagina}")
        
        fuentes_formateadas = "\n".join(fuentes_texto) if fuentes_texto else "No hay fuentes disponibles"
        
        return {
            "respuesta": respuesta,
            "fuentes": fuentes_formateadas,
            "bloqueada": False
        }
        
    except Exception as e:
        return {
            "respuesta": f"Error al procesar la consulta: {str(e)}",
            "fuentes": "Error al obtener fuentes",
            "bloqueada": False
        }


@app.websocket("/_event")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        print("Cliente WebSocket desconectado")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8005)