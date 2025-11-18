# Migración de ChromaDB a Qdrant

## Resumen

Este documento describe la migración de ChromaDB a Qdrant como base de datos vectorial para el servicio de búsqueda semántica.

## Fecha de Migración

**Versión:** 2.0.0  
**Fecha:** 2024

## Cambios Realizados

### 1. Base de Datos Vectorial

- **Antes:** ChromaDB (local, basado en archivos)
- **Después:** Qdrant (servidor dedicado, más escalable)

### 2. Configuración

#### Variables de Entorno Nuevas

```bash
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
QDRANT_COLLECTION_NAME=saved_queries
```

#### Variables Deprecadas

```bash
CHROMA_DB_PATH=./data/chroma_db  # DEPRECATED - Ya no se usa
```

### 3. Dependencias

#### Removidas

- `chromadb==1.2.1` - Completamente removido de requirements.txt

#### Agregadas

- `qdrant-client==1.7.3` - Cliente oficial de Qdrant

### 4. Código Deprecado

#### En `app/config/settings.py`

- `chroma_db_path`: Marcado como DEPRECATED pero mantenido para compatibilidad
- `ensure_chroma_db_directory()`: Marcado como DEPRECATED con warning

### 5. Servicios Actualizados

#### `app/services/qdrant_service.py` (NUEVO)

- Servicio completo para interactuar con Qdrant
- Operaciones CRUD: upsert, delete, search
- Health checks y manejo de errores

#### `app/services/search_service.py` (ACTUALIZADO)

- Refactorizado para usar QdrantService
- Eliminadas todas las referencias a ChromaDB
- Nuevos métodos: `upsert_query()`, `delete_query()`

### 6. Endpoints Nuevos

- `POST /api/v1/consultas/upsert` - Sincronizar consulta guardada
- `DELETE /api/v1/consultas/{query_id}` - Eliminar consulta guardada

## Beneficios de la Migración

1. **Escalabilidad**: Qdrant es más escalable que ChromaDB
2. **Rendimiento**: Mejor rendimiento en búsquedas vectoriales
3. **Características**: Más opciones de filtrado y búsqueda
4. **Producción**: Mejor soporte para entornos de producción
5. **CRUD Completo**: Soporte nativo para operaciones de actualización y eliminación

## Compatibilidad Hacia Atrás

### Variables de Entorno

La variable `CHROMA_DB_PATH` se mantiene en el código pero está marcada como DEPRECATED. No afecta el funcionamiento de la aplicación.

### Datos Existentes

Los datos de ChromaDB NO se migran automáticamente. Si necesitas migrar datos existentes:

1. Usa el script de migración (si está disponible)
2. O re-indexa los datos desde la fuente original

## Pasos para Actualizar

### 1. Instalar Qdrant

#### Opción A: Docker (Recomendado)

```bash
docker run -p 6333:6333 qdrant/qdrant
```

#### Opción B: Docker Compose

```yaml
services:
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - ./data/qdrant_storage:/qdrant/storage
```

### 2. Actualizar Variables de Entorno

Agregar al archivo `.env`:

```bash
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
QDRANT_COLLECTION_NAME=saved_queries
```

### 3. Actualizar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Reiniciar la Aplicación

```bash
# La aplicación creará automáticamente la colección en Qdrant
python main.py
```

## Verificación

### 1. Health Check

```bash
curl http://localhost:8000/api/v1/health
```

Debe mostrar:

```json
{
  "status": "healthy",
  "services": {
    "qdrant": {
      "status": "healthy",
      "collection_exists": true
    }
  }
}
```

### 2. Logs de Startup

Buscar en los logs:

```
Conexión a Qdrant establecida exitosamente
Colección creada exitosamente
```

## Rollback (Si es Necesario)

Si necesitas volver a ChromaDB:

1. Revertir a la versión anterior del código (< 2.0.0)
2. Restaurar `chromadb` en requirements.txt
3. Restaurar el código de SearchService anterior

**NOTA:** No recomendado. Qdrant es la solución a largo plazo.

## Soporte

Para problemas o preguntas sobre la migración, consultar:

- Documentación de Qdrant: https://qdrant.tech/documentation/
- Issues del proyecto
- Equipo de desarrollo

## Notas Adicionales

- La colección en Qdrant se crea automáticamente en el startup
- Los embeddings siguen usando el mismo modelo de OpenAI (text-embedding-3-small)
- La dimensión de vectores es 1536 (compatible con OpenAI)
- La métrica de distancia es COSINE (igual que antes)
