# buscar_triage.py
import chromadb

client = chromadb.PersistentClient(path="chroma_db")
collection = client.get_collection("libros_medicos")

print("🔍 Buscando 'triage' en los libros...")
print("=" * 60)

resultados = collection.query(
    query_texts=["triage clasificación pacientes emergencia"],
    n_results=10
)

if resultados["documents"] and resultados["documents"][0]:
    print(f"\n📚 Encontrados {len(resultados['documents'][0])} fragmentos:\n")
    for i, (doc, meta) in enumerate(zip(resultados['documents'][0], resultados['metadatas'][0])):
        print(f"{i+1}. 📖 {meta.get('libro', 'Desconocido')} - Página {meta.get('pagina', '?')}")
        print(f"   📝 {doc[:400]}...")
        print("-" * 60)
else:
    print("❌ No se encontraron fragmentos relacionados con 'triage'.")