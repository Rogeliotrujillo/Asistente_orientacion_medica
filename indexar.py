# indexar.py
import os
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
import chromadb
import chromadb.utils.embedding_functions as embedding_functions

# ==========================================
# CONFIGURACIÓN
# ==========================================
PDF_PATH = "documentos/"
CHROMA_PATH = "chroma_db"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

print("📦 Cargando modelo de embeddings...")
model = SentenceTransformer('all-MiniLM-L6-v2')

def leer_pdf(ruta_archivo):
    """Lee un PDF y devuelve el texto de cada página con su número"""
    print(f"📄 Leyendo: {ruta_archivo}")
    reader = PdfReader(ruta_archivo)
    paginas = []
    for i, pagina in enumerate(reader.pages):
        texto = pagina.extract_text()
        if texto.strip():
            paginas.append({
                "numero": i,  # 🔧 CAMBIO: i en lugar de i+1 (empieza en 0)
                "texto": texto.strip()
            })
    return paginas

def dividir_en_fragmentos(texto, tamaño, solapamiento):
    """Divide un texto largo en fragmentos con solapamiento"""
    fragmentos = []
    inicio = 0
    while inicio < len(texto):
        fin = min(inicio + tamaño, len(texto))
        fragmento = texto[inicio:fin]
        fragmentos.append(fragmento)
        inicio += tamaño - solapamiento
        if inicio >= len(texto):
            break
    return fragmentos

def procesar_pdfs():
    """Procesa todos los PDFs en la carpeta documentos/"""
    todos_los_fragmentos = []
    
    archivos = [f for f in os.listdir(PDF_PATH) if f.lower().endswith('.pdf')]
    
    if not archivos:
        print("❌ No se encontraron PDFs en la carpeta 'documentos/'")
        return []
    
    print(f"📚 Encontrados {len(archivos)} PDFs")
    
    for archivo in archivos:
        ruta_completa = os.path.join(PDF_PATH, archivo)
        paginas = leer_pdf(ruta_completa)
        
        for pagina in paginas:
            fragmentos = dividir_en_fragmentos(
                pagina["texto"], 
                CHUNK_SIZE, 
                CHUNK_OVERLAP
            )
            
            for i, frag in enumerate(fragmentos):
                todos_los_fragmentos.append({
                    "texto": frag,
                    "libro": archivo,
                    "pagina": pagina["numero"],
                    "fragmento_id": f"{archivo}_pag{pagina['numero']}_frag{i+1}"
                })
    
    print(f"✅ Generados {len(todos_los_fragmentos)} fragmentos")
    return todos_los_fragmentos

def guardar_en_chromadb(fragmentos):
    """Guarda los fragmentos en ChromaDB con sus embeddings"""
    print("💾 Guardando en ChromaDB...")
    
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    
    try:
        client.delete_collection("libros_medicos")
    except:
        pass
    
    collection = client.create_collection(
        name="libros_medicos",
        embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
    )
    
    textos = [f["texto"] for f in fragmentos]
    metadatos = [
        {
            "libro": f["libro"],
            "pagina": f["pagina"],
            "fragmento_id": f["fragmento_id"]
        }
        for f in fragmentos
    ]
    ids = [f["fragmento_id"] for f in fragmentos]
    
    batch_size = 100
    for i in range(0, len(textos), batch_size):
        fin = min(i + batch_size, len(textos))
        collection.add(
            documents=textos[i:fin],
            metadatas=metadatos[i:fin],
            ids=ids[i:fin]
        )
        print(f"   ✅ Lote {i//batch_size + 1}: {fin-i} fragmentos guardados")
    
    print(f"🎉 ¡Indexación completada! {len(textos)} fragmentos en ChromaDB")
    return collection

if __name__ == "__main__":
    print("=" * 50)
    print("📚 INDEXACIÓN DE LIBROS MÉDICOS")
    print("=" * 50)
    
    fragmentos = procesar_pdfs()
    if fragmentos:
        collection = guardar_en_chromadb(fragmentos)
        print(f"\n✅ ¡Proceso completado con éxito!")
        print(f"   📁 ChromaDB guardada en: {CHROMA_PATH}")
    else:
        print("❌ No se procesó ningún archivo.")