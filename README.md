# Asistente de Orientación Médica Universitaria

Asistente virtual basado en RAG (Retrieval-Augmented Generation) que responde preguntas médicas utilizando 6 libros de texto universitarios.

## Tecnologías

- **Frontend**: Reflex (Python)
- **Backend**: FastAPI
- **Base de datos vectorial**: ChromaDB
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **IA**: Google Gemini (gemini-2.5-flash-lite)

## Instalación

```bash
# Clonar repositorio
git clone https://github.com/Rogeliotrujillo/Asistente_orientacion_medica.git
cd Asistente_orientacion_medica

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt

# Indexar libros
python indexar.py

# Ejecutar backend
uvicorn backend:app --reload --port 8005

# Ejecutar frontend (otra terminal)
reflex run
