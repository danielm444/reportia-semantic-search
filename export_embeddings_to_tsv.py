"""
Script para exportar embeddings de Qdrant a formato TSV para TensorFlow Projector
https://projector.tensorflow.org/
"""
import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient

# Cargar variables de entorno
load_dotenv()

def export_embeddings_to_tsv(collection_name: str, output_dir: str = "embeddings_export"):
    """
    Exporta embeddings de Qdrant a archivos TSV para TensorFlow Projector
    
    Args:
        collection_name: Nombre de la colección en Qdrant
        output_dir: Directorio donde guardar los archivos TSV
    """
    # Conectar a Qdrant
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    client = QdrantClient(url=qdrant_url)
    
    # Crear directorio de salida
    os.makedirs(output_dir, exist_ok=True)
    
    # Obtener todos los puntos de la colección
    print(f"Obteniendo puntos de la colección '{collection_name}'...")
    
    # Scroll para obtener todos los puntos
    points = []
    offset = None
    
    while True:
        result = client.scroll(
            collection_name=collection_name,
            limit=100,
            offset=offset,
            with_payload=True,
            with_vectors=True
        )
        
        points.extend(result[0])
        offset = result[1]
        
        if offset is None:
            break
    
    print(f"Total de puntos obtenidos: {len(points)}")
    
    # Archivos de salida
    vectors_file = os.path.join(output_dir, "vectors.tsv")
    metadata_file = os.path.join(output_dir, "metadata.tsv")
    
    # Escribir vectores
    print(f"Escribiendo vectores en {vectors_file}...")
    with open(vectors_file, 'w', encoding='utf-8') as f:
        for point in points:
            vector = point.vector
            # Escribir cada dimensión separada por tabulador
            f.write('\t'.join(map(str, vector)) + '\n')
    
    # Helpers de limpieza y etiquetado genérico
    def clean(value) -> str:
        return str(value).replace('\t', ' ').replace('\n', ' ').replace('\r', ' ')

    def build_label(payload: dict, point_id) -> str:
        """Etiqueta legible, agnóstica de dominio (menú o saved queries)."""
        titulo = payload.get('titulo') or payload.get('name') or payload.get('Nivel0')
        desc = payload.get('Descripcion') or payload.get('description')
        if titulo and desc:
            return f"{titulo}: {desc}"
        return titulo or desc or str(point_id)

    # Escribir metadata
    print(f"Escribiendo metadata en {metadata_file}...")
    with open(metadata_file, 'w', encoding='utf-8') as f:
        # Encabezados - 'label' e 'id' primero; el resto son las claves del payload
        # (unión de todas las claves presentes, para ser robusto ante payloads heterogéneos)
        payload_keys = []
        for point in points:
            for k in (point.payload or {}).keys():
                if k not in payload_keys:
                    payload_keys.append(k)

        headers = ['label', 'id'] + payload_keys
        f.write('\t'.join(headers) + '\n')

        # Datos
        for point in points:
            payload = point.payload or {}
            row = [clean(build_label(payload, point.id)), clean(point.id)]
            for key in payload_keys:
                row.append(clean(payload.get(key, '')))
            f.write('\t'.join(row) + '\n')
    
    print(f"\n✅ Exportación completada!")
    print(f"📁 Archivos generados en: {output_dir}/")
    print(f"   - vectors.tsv: {len(points)} vectores")
    print(f"   - metadata.tsv: {len(points)} filas de metadata")
    print(f"\n📊 Para visualizar en TensorFlow Projector:")
    print(f"   1. Ve a https://projector.tensorflow.org/")
    print(f"   2. Click en 'Load' en la esquina superior izquierda")
    print(f"   3. Sube vectors.tsv como 'Choose file' (embeddings)")
    print(f"   4. Sube metadata.tsv como 'Load a TSV metadata file'")

if __name__ == "__main__":
    # Nombre de la colección (desde .env, con fallback)
    COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "saved_queries")

    export_embeddings_to_tsv(COLLECTION_NAME)
