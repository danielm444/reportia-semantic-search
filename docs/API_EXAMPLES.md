# Ejemplos de Uso de la API

Este documento proporciona ejemplos prácticos de uso de todos los endpoints de la API de Búsqueda Semántica.

## Tabla de Contenidos

- [Autenticación](#autenticación)
- [Endpoints de Búsqueda](#endpoints-de-búsqueda)
- [Endpoints de Sincronización](#endpoints-de-sincronización)
- [Endpoints de Información](#endpoints-de-información)
- [Ejemplos con Diferentes Lenguajes](#ejemplos-con-diferentes-lenguajes)

## Autenticación

Todos los endpoints protegidos requieren el header `X-API-Key`:

```bash
X-API-Key: tu_clave_api_aqui
```

## Endpoints de Búsqueda

### POST /api/v1/buscar

Realiza búsqueda semántica sobre consultas guardadas.

#### Ejemplo Básico

```bash
curl -X POST "http://localhost:8000/api/v1/buscar" \
  -H "X-API-Key: tu_clave_api" \
  -H "Content-Type: application/json" \
  -d '{
    "pregunta": "reportes de ventas mensuales",
    "top_k": 3
  }'
```

#### Respuesta

```json
{
  "resultados": [
    {
      "data": {
        "id": 123,
        "name": "Reporte de ventas mensuales",
        "description": "Consulta que genera reporte de ventas por mes y región",
        "query_sql_original": "SELECT * FROM sales WHERE month = ?",
        "query_sql_param": "SELECT * FROM sales WHERE month = :month",
        "parameters_json": {"month": {"type": "integer", "default": 1}},
        "engine_code": "postgres",
        "company_id": 456,
        "owner_user_id": 789,
        "version": 1,
        "is_active": true,
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z"
      },
      "score": 0.8547
    },
    {
      "data": {
        "id": 124,
        "name": "Análisis de ventas por producto",
        "description": "Consulta de ventas detallada por producto",
        "query_sql_original": "SELECT * FROM sales WHERE product_id = ?",
        "engine_code": "postgres",
        "company_id": 456,
        "owner_user_id": 789,
        "version": 1,
        "is_active": true,
        "created_at": "2024-01-15T11:00:00Z",
        "updated_at": "2024-01-15T11:00:00Z"
      },
      "score": 0.7234
    }
  ],
  "total": 2,
  "tiempo_respuesta": 0.245,
  "consulta": "reportes de ventas mensuales",
  "timestamp": "2024-01-15T12:00:00Z"
}
```

#### Ejemplo con Más Resultados

```bash
curl -X POST "http://localhost:8000/api/v1/buscar" \
  -H "X-API-Key: tu_clave_api" \
  -H "Content-Type: application/json" \
  -d '{
    "pregunta": "consultas de inventario",
    "top_k": 10
  }'
```

## Endpoints de Sincronización

### POST /api/v1/consultas/upsert

Crea o actualiza una consulta guardada en la base de datos vectorial.

#### Ejemplo: Crear Nueva Consulta

```bash
curl -X POST "http://localhost:8000/api/v1/consultas/upsert" \
  -H "X-API-Key: tu_clave_api" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "id": 125,
      "name": "Reporte de inventario bajo",
      "description": "Consulta que muestra productos con inventario por debajo del mínimo",
      "query_sql_original": "SELECT * FROM products WHERE stock < min_stock",
      "query_sql_param": "SELECT * FROM products WHERE stock < :min_stock",
      "parameters_json": {
        "min_stock": {
          "type": "integer",
          "default": 10,
          "description": "Stock mínimo"
        }
      },
      "engine_code": "postgres",
      "company_id": 456,
      "owner_user_id": 789,
      "version": 1,
      "is_active": true,
      "created_at": "2024-01-15T14:00:00Z",
      "updated_at": "2024-01-15T14:00:00Z"
    }
  }'
```

#### Respuesta

```json
{
  "id": 125,
  "status": "success",
  "message": "Consulta sincronizada exitosamente",
  "timestamp": "2024-01-15T14:00:05Z"
}
```

#### Ejemplo: Actualizar Consulta Existente

```bash
curl -X POST "http://localhost:8000/api/v1/consultas/upsert" \
  -H "X-API-Key: tu_clave_api" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "id": 125,
      "name": "Reporte de inventario crítico",
      "description": "Consulta actualizada que muestra productos con inventario crítico",
      "query_sql_original": "SELECT * FROM products WHERE stock < min_stock AND is_critical = true",
      "query_sql_param": "SELECT * FROM products WHERE stock < :min_stock AND is_critical = :is_critical",
      "parameters_json": {
        "min_stock": {
          "type": "integer",
          "default": 5
        },
        "is_critical": {
          "type": "boolean",
          "default": true
        }
      },
      "engine_code": "postgres",
      "company_id": 456,
      "owner_user_id": 789,
      "version": 2,
      "is_active": true,
      "created_at": "2024-01-15T14:00:00Z",
      "updated_at": "2024-01-15T15:00:00Z"
    }
  }'
```

### DELETE /api/v1/consultas/{query_id}

Elimina una consulta guardada de la base de datos vectorial.

#### Ejemplo: Eliminar Consulta

```bash
curl -X DELETE "http://localhost:8000/api/v1/consultas/125" \
  -H "X-API-Key: tu_clave_api"
```

#### Respuesta Exitosa

```
HTTP/1.1 204 No Content
```

#### Respuesta: Consulta No Encontrada

```json
{
  "error": "QUERY_NOT_FOUND",
  "message": "Consulta con ID 125 no encontrada",
  "timestamp": "2024-01-15T15:30:00Z",
  "path": "/api/v1/consultas/125",
  "details": {
    "query_id": 125
  }
}
```

## Endpoints de Información

### GET /api/v1/health

Health check detallado con información de servicios.

#### Ejemplo

```bash
curl -X GET "http://localhost:8000/api/v1/health" \
  -H "X-API-Key: tu_clave_api"
```

#### Respuesta

```json
{
  "status": "healthy",
  "version": "2.0.0",
  "timestamp": "2024-01-15T16:00:00Z",
  "services": {
    "embedding_service": {
      "status": "healthy",
      "provider": "OpenAI"
    },
    "qdrant": {
      "status": "healthy",
      "url": "http://localhost:6333",
      "collection_name": "saved_queries",
      "collection_exists": true,
      "collection_info": {
        "vectors_count": 150,
        "points_count": 150,
        "status": "green"
      }
    },
    "search_service": {
      "status": "healthy"
    }
  }
}
```

### GET /api/v1/info

Información general de la API.

#### Ejemplo

```bash
curl -X GET "http://localhost:8000/api/v1/info" \
  -H "X-API-Key: tu_clave_api"
```

#### Respuesta

```json
{
  "api_version": "v1",
  "app_version": "2.0.0",
  "app_name": "Reportia Semantic Search API",
  "endpoints": {
    "search": {
      "path": "/v1/buscar",
      "method": "POST",
      "description": "Búsqueda semántica de consultas guardadas"
    },
    "upsert": {
      "path": "/v1/consultas/upsert",
      "method": "POST",
      "description": "Crear o actualizar consulta guardada"
    },
    "delete": {
      "path": "/v1/consultas/{query_id}",
      "method": "DELETE",
      "description": "Eliminar consulta guardada"
    },
    "health": {
      "path": "/v1/health",
      "method": "GET",
      "description": "Health check detallado"
    },
    "info": {
      "path": "/v1/info",
      "method": "GET",
      "description": "Información de la API"
    }
  },
  "search_capabilities": {
    "max_results": 20,
    "max_query_length": 1000,
    "supported_languages": ["es", "en"],
    "vector_store": "Qdrant",
    "embedding_model": "text-embedding-3-small"
  },
  "sync_capabilities": {
    "upsert": "Sincronización automática desde savedquery_service",
    "delete": "Eliminación sincronizada con BD relacional",
    "idempotent": true
  },
  "collection_info": {
    "collection_name": "saved_queries",
    "vectors_count": 150,
    "points_count": 150,
    "status": "green",
    "vector_size": 1536,
    "distance": "COSINE"
  },
  "authentication": {
    "type": "API Key",
    "header": "X-API-Key",
    "required": true
  },
  "documentation": "/docs"
}
```

## Ejemplos con Diferentes Lenguajes

### Python

```python
import requests

API_URL = "http://localhost:8000"
API_KEY = "tu_clave_api"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Búsqueda
response = requests.post(
    f"{API_URL}/api/v1/buscar",
    headers=headers,
    json={
        "pregunta": "reportes de ventas",
        "top_k": 5
    }
)
print(response.json())

# Upsert
response = requests.post(
    f"{API_URL}/api/v1/consultas/upsert",
    headers=headers,
    json={
        "query": {
            "id": 126,
            "name": "Nueva consulta",
            "description": "Descripción de la consulta",
            "query_sql_original": "SELECT * FROM table",
            "engine_code": "postgres",
            "company_id": 1,
            "owner_user_id": 1,
            "is_active": True,
            "created_at": "2024-01-15T10:00:00Z",
            "updated_at": "2024-01-15T10:00:00Z"
        }
    }
)
print(response.json())

# Delete
response = requests.delete(
    f"{API_URL}/api/v1/consultas/126",
    headers=headers
)
print(response.status_code)  # 204 si exitoso
```

### JavaScript (Node.js)

```javascript
const axios = require('axios');

const API_URL = 'http://localhost:8000';
const API_KEY = 'tu_clave_api';

const headers = {
  'X-API-Key': API_KEY,
  'Content-Type': 'application/json'
};

// Búsqueda
async function buscar() {
  const response = await axios.post(
    `${API_URL}/api/v1/buscar`,
    {
      pregunta: 'reportes de ventas',
      top_k: 5
    },
    { headers }
  );
  console.log(response.data);
}

// Upsert
async function upsert() {
  const response = await axios.post(
    `${API_URL}/api/v1/consultas/upsert`,
    {
      query: {
        id: 126,
        name: 'Nueva consulta',
        description: 'Descripción de la consulta',
        query_sql_original: 'SELECT * FROM table',
        engine_code: 'postgres',
        company_id: 1,
        owner_user_id: 1,
        is_active: true,
        created_at: '2024-01-15T10:00:00Z',
        updated_at: '2024-01-15T10:00:00Z'
      }
    },
    { headers }
  );
  console.log(response.data);
}

// Delete
async function eliminar() {
  const response = await axios.delete(
    `${API_URL}/api/v1/consultas/126`,
    { headers }
  );
  console.log(response.status);  // 204 si exitoso
}

buscar();
upsert();
eliminar();
```

### TypeScript (React)

```typescript
interface SearchRequest {
  pregunta: string;
  top_k: number;
}

interface SearchResult {
  data: {
    id: number;
    name: string;
    description?: string;
    query_sql_original: string;
    // ... otros campos
  };
  score: number;
}

interface SearchResponse {
  resultados: SearchResult[];
  total: number;
  tiempo_respuesta: number;
  consulta: string;
  timestamp: string;
}

const API_URL = 'http://localhost:8000';
const API_KEY = 'tu_clave_api';

async function buscarConsultas(pregunta: string, topK: number = 5): Promise<SearchResponse> {
  const response = await fetch(`${API_URL}/api/v1/buscar`, {
    method: 'POST',
    headers: {
      'X-API-Key': API_KEY,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      pregunta,
      top_k: topK
    })
  });

  if (!response.ok) {
    throw new Error(`Error: ${response.status}`);
  }

  return response.json();
}

// Uso en componente React
function SearchComponent() {
  const [resultados, setResultados] = useState<SearchResult[]>([]);

  const handleSearch = async (query: string) => {
    try {
      const data = await buscarConsultas(query, 5);
      setResultados(data.resultados);
    } catch (error) {
      console.error('Error en búsqueda:', error);
    }
  };

  return (
    <div>
      {resultados.map(resultado => (
        <div key={resultado.data.id}>
          <h3>{resultado.data.name}</h3>
          <p>Score: {resultado.score.toFixed(4)}</p>
          <p>{resultado.data.description}</p>
        </div>
      ))}
    </div>
  );
}
```

## Manejo de Errores

### Ejemplo de Manejo de Errores en Python

```python
import requests
from requests.exceptions import RequestException

def buscar_con_manejo_errores(pregunta: str, top_k: int = 5):
    try:
        response = requests.post(
            f"{API_URL}/api/v1/buscar",
            headers=headers,
            json={"pregunta": pregunta, "top_k": top_k},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("Error: API Key inválida")
        elif e.response.status_code == 422:
            print("Error: Parámetros inválidos")
            print(e.response.json())
        elif e.response.status_code == 503:
            print("Error: Servicio no disponible")
        else:
            print(f"Error HTTP: {e.response.status_code}")
        return None
    
    except RequestException as e:
        print(f"Error de conexión: {e}")
        return None
```

## Casos de Uso Completos

### Caso 1: Sincronización desde SavedQuery Service

```python
def sincronizar_consulta_guardada(consulta_db):
    """
    Sincroniza una consulta desde la BD relacional a Qdrant
    """
    payload = {
        "query": {
            "id": consulta_db.id,
            "name": consulta_db.name,
            "description": consulta_db.description,
            "query_sql_original": consulta_db.query_sql_original,
            "query_sql_param": consulta_db.query_sql_param,
            "parameters_json": consulta_db.parameters_json,
            "engine_code": consulta_db.engine_code,
            "company_id": consulta_db.company_id,
            "owner_user_id": consulta_db.owner_user_id,
            "version": consulta_db.version,
            "is_active": consulta_db.is_active,
            "created_at": consulta_db.created_at.isoformat(),
            "updated_at": consulta_db.updated_at.isoformat()
        }
    }
    
    response = requests.post(
        f"{API_URL}/api/v1/consultas/upsert",
        headers=headers,
        json=payload
    )
    
    if response.status_code == 200:
        print(f"Consulta {consulta_db.id} sincronizada exitosamente")
    else:
        print(f"Error sincronizando consulta: {response.text}")
```

### Caso 2: Búsqueda con Filtrado por Score

```python
def buscar_con_filtro_score(pregunta: str, min_score: float = 0.7):
    """
    Busca consultas y filtra por score mínimo
    """
    response = requests.post(
        f"{API_URL}/api/v1/buscar",
        headers=headers,
        json={"pregunta": pregunta, "top_k": 20}
    )
    
    if response.status_code == 200:
        data = response.json()
        resultados_filtrados = [
            r for r in data["resultados"]
            if r["score"] >= min_score
        ]
        return resultados_filtrados
    
    return []
```

## Documentación Interactiva

Para explorar todos los endpoints de forma interactiva, visita:

```
http://localhost:8000/docs
```

La documentación Swagger UI permite:
- Probar endpoints directamente desde el navegador
- Ver esquemas de request/response
- Autenticarse con tu API Key
- Ver ejemplos de uso
