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
    
    # Escribir metadata
    print(f"Escribiendo metadata en {metadata_file}...")
    with open(metadata_file, 'w', encoding='utf-8') as f:
        # Encabezados - ponemos 'label' primero para que sea la columna principal
        if points:
            sample_payload = points[0].payload
            # 'label' será la primera columna que muestra TensorFlow Projector
            headers = ['label', 'id', 'name', 'description'] + [k for k in sample_payload.keys() if k not in ['name', 'description']]
            f.write('\t'.join(headers) + '\n')
        
        # Datos
        for point in points:
            name = point.payload.get('name', '')
            description = point.payload.get('description', '')
            
            # Crear label combinando name y description
            label = f"{name}: {description}" if name and description else name or description or str(point.id)
            # Limpiar el label
            label = label.replace('\t', ' ').replace('\n', ' ').replace('\r', ' ')
            
            row = [label, str(point.id)]
            
            # Agregar name y description
            for key in ['name', 'description']:
                value = point.payload.get(key, '')
                value_str = str(value).replace('\t', ' ').replace('\n', ' ').replace('\r', ' ')
                row.append(value_str)
            
            # Agregar el resto de campos
            for key in headers[4:]:
                value = point.payload.get(key, '')
                value_str = str(value).replace('\t', ' ').replace('\n', ' ').replace('\r', ' ')
                row.append(value_str)
            
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
    # Nombre de tu colección
    COLLECTION_NAME = "saved_queries"  # Cambia esto si tu colección tiene otro nombre
    
    export_embeddings_to_tsv(COLLECTION_NAME)
