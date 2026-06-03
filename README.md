# API de Búsqueda Semántica MENU

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![LangChain](https://img.shields.io/badge/LangChain-0.0.350+-orange.svg)](https://langchain.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)

Microservicio RESTful en Python que proporciona búsqueda semántica sobre catálogos de datos estructurados usando LangChain, OpenAI y Qdrant.

## 🚀 Características

- **Núcleo Genérico**: Indexa cualquier documento (`id` + `texto` + `payload` libre); la búsqueda devuelve el **payload completo**. Sirve para menús de navegación, consultas SQL guardadas o cualquier catálogo.
- **Búsqueda Semántica**: Consultas en lenguaje natural con similarity scores, **filtros por payload**, **umbral de score** y **paginación**.
- **Base de Datos Vectorial**: Qdrant para búsquedas vectoriales escalables y eficientes
- **Sincronización CRUD**: Endpoints para crear, actualizar y eliminar (individual y **en lote/batch**)
- **Rendimiento**: Caché LRU de embeddings de consultas + upsert/embeddings en lote
- **Arquitectura Modular**: Servicios desacoplados para embeddings, búsqueda y Qdrant
- **Autenticación**: API Key con `401`/`403` diferenciados y comparación en tiempo constante
- **Calidad**: Suite de tests `pytest` que corre sin red (Qdrant en memoria + embeddings fake), Pydantic v2, `lifespan` moderno
- **Containerización**: Docker y Docker Compose listos para producción
- **Health Checks** y **OpenAPI 3.0+** con Swagger UI

## 📋 Tabla de Contenidos

- [Instalación](#-instalación)
- [Configuración](#-configuración)
- [Uso](#-uso)
- [API Endpoints](#-api-endpoints)
- [Indexación](#-indexación)
- [Docker](#-docker)
- [Desarrollo](#-desarrollo)
- [Despliegue](#-despliegue)
- [Contribución](#-contribución)

## 🛠 Instalación

### Requisitos

- Python 3.11+
- OpenAI API Key
- Qdrant (servidor local o remoto)
- Docker (opcional pero recomendado)

### Instalación Local

```bash
# 1. Clonar repositorio
git clone <repository-url>
cd menu-api

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus claves reales
```

### Instalación con Docker (Recomendado)

```bash
# 1. Clonar repositorio
git clone <repository-url>
cd menu-api

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus claves reales

# 3. Iniciar servicios (incluye Qdrant)
docker-compose up -d
```

El archivo `docker-compose.yml` incluye:
- **API**: Servicio principal de búsqueda semántica
- **Qdrant**: Base de datos vectorial (puerto 6333)

### Configurar Qdrant

#### Opción 1: Docker (Incluido en docker-compose)

El servicio de Qdrant se inicia automáticamente con `docker-compose up -d`.

#### Opción 2: Docker Standalone

```bash
docker run -p 6333:6333 -v $(pwd)/data/qdrant_storage:/qdrant/storage qdrant/qdrant
```

#### Opción 3: Instalación Local

Ver [documentación de Qdrant](https://qdrant.tech/documentation/quick-start/) para instalación local.

#### Opción 4: Qdrant Cloud

1. Crear cuenta en [Qdrant Cloud](https://cloud.qdrant.io/)
2. Crear cluster
3. Configurar en `.env`:
   ```bash
   QDRANT_URL=https://tu-cluster.qdrant.io
   QDRANT_API_KEY=tu_api_key
   ```

## ⚙️ Configuración

### Variables de Entorno

Crear archivo `.env` basado en `.env.example`:

```bash
# API Configuration
MENU_API_KEY=tu_clave_secreta_aqui
CORS_ALLOWED_ORIGINS=https://tu-dominio.com,http://localhost:3000

# OpenAI Configuration  
OPENAI_API_KEY=sk-tu_clave_openai_real

# Qdrant Configuration
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
QDRANT_COLLECTION_NAME=saved_queries

# Database Configuration (DEPRECATED - mantener para compatibilidad)
CHROMA_DB_PATH=./data/chroma_db

# Logging Configuration
LOG_LEVEL=INFO

# Server Configuration
HOST=0.0.0.0
PORT=8000
```

### Estructura del Archivo menu.json

El sistema indexa datos desde `data/menu.json` con la siguiente estructura:

```json
[
  {
    "ID": 1,
    "Nivel0": "Configuración",
    "Nivel1": "Sistema",
    "Descripcion": "Configurar parámetros generales del sistema",
    "url": "localhost/config/sistema"
  },
  {
    "ID": 2,
    "Nivel0": "Configuración", 
    "Nivel1": "Alertas",
    "Descripcion": "Configura las notificaciones y alertas del sistema",
    "url": "localhost/config/alertas"
  }
]
```

**Campos requeridos:**
- `ID` (integer): Identificador único
- `Nivel0` (string): Categoría principal
- `Descripcion` (string): Descripción del elemento
- `url` (string): URL del elemento

**Campos opcionales:**
- `Nivel1` (string): Subcategoría
- `keywords` (array): Palabras clave adicionales

## 🎯 Uso

### Iniciar el Servidor

```bash
# Desarrollo
python main.py

# Producción
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app -b 0.0.0.0:8000
```

### Indexar Datos

```bash
# Indexación básica
python indexar.py

# Con opciones
python indexar.py --file data/custom.json --verbose

# Modo dry-run (solo validar)
python indexar.py --dry-run
```

### Realizar Búsquedas

```bash
# Usando curl
curl -X POST "http://localhost:8000/api/v1/buscar" \
  -H "X-API-Key: tu_clave_api" \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "¿dónde configuro alertas?", "top_k": 3}'

# Respuesta
{
  "resultados": [
    {
      "ID": 2,
      "Nivel0": "Configuración",
      "Nivel1": "Alertas",
      "Descripcion": "Configura las notificaciones y alertas del sistema",
      "url": "localhost/config/alertas"
    }
  ],
  "total": 1,
  "tiempo_respuesta": 0.245,
  "consulta": "¿dónde configuro alertas?",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## 📡 API Endpoints

### Endpoints Públicos

- `GET /` - Información general de la API
- `GET /health` - Health check básico
- `GET /versions` - Información de versiones disponibles
- `GET /docs` - Documentación interactiva (Swagger UI)

### API v1 (Requiere Autenticación)

#### Endpoints de Búsqueda
- `POST /api/v1/buscar` - Búsqueda semántica con scores, filtros, umbral y paginación

#### Endpoints de Documentos Genéricos (CRUD)
- `POST /api/v1/documentos/upsert` - Crear o actualizar un documento genérico
- `POST /api/v1/documentos/upsert/batch` - Crear o actualizar documentos en lote
- `DELETE /api/v1/documentos/{doc_id}` - Eliminar un documento (id int o string)

#### Endpoints de Consultas Guardadas (compatibilidad saved_query)
- `POST /api/v1/consultas/upsert` - Crear o actualizar consulta guardada
- `POST /api/v1/consultas/upsert/batch` - Crear o actualizar consultas en lote
- `DELETE /api/v1/consultas/{query_id}` - Eliminar consulta guardada

#### Endpoints de Información
- `GET /api/v1/health` - Health check detallado
- `GET /api/v1/info` - Información de la API v1

> **Modelo de datos genérico**: la base vectorial almacena documentos
> `{ id, texto, payload }`. El `texto` se vectoriza; el `payload` (cualquier
> estructura) se guarda y se devuelve **íntegro** en `data` al buscar. Los
> endpoints de `consultas` son adaptadores sobre este núcleo.

### Búsqueda Semántica con Similarity Scores

El endpoint `/api/v1/buscar` incluye **similarity scores** y parámetros opcionales
de filtrado, umbral y paginación:

```json
{
  "pregunta": "¿dónde configuro alertas?",
  "top_k": 3,
  "score_threshold": 0.5,
  "filtros": { "tipo": "configuration" },
  "offset": 0
}
```

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `pregunta` | string | — | Consulta en lenguaje natural (1-1000 chars) |
| `top_k` | int | 3 | Número de resultados (1-20) |
| `score_threshold` | float? | `null` | Descarta resultados por debajo del umbral (0-1) |
| `filtros` | object? | `null` | Igualdad sobre el payload; AND entre campos, lista = OR |
| `offset` | int | 0 | Resultados a saltar (paginación) |

**Respuesta con Scores:**
```json
{
  "resultados": [
    {
      "data": {
        "ID": 2,
        "Nivel0": "Configuración",
        "Nivel1": "Alertas",
        "Descripcion": "Configura las notificaciones y alertas del sistema",
        "url": "localhost/config/alertas"
      },
      "score": 0.8547
    },
    {
      "data": {
        "ID": 1,
        "Nivel0": "Configuración",
        "Nivel1": "Sistema",
        "Descripcion": "Configurar parámetros generales del sistema",
        "url": "localhost/config/sistema"
      },
      "score": 0.6234
    }
  ],
  "total": 2,
  "tiempo_respuesta": 0.245,
  "consulta": "¿dónde configuro alertas?",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### Interpretación de Similarity Scores

Los **similarity scores** indican qué tan similar semánticamente es cada resultado a tu consulta. El sistema utiliza embeddings de OpenAI y distancia coseno normalizada para calcular estos valores.

| Rango | Indicador | Interpretación | Recomendación |
|-------|-----------|----------------|---------------|
| **0.9-1.0** | 🟢 **Muy Alta** | Coincidencia casi exacta con la consulta | Resultado altamente confiable |
| **0.7-0.9** | 🟡 **Alta** | Muy relevante para la consulta | Resultado muy recomendado |
| **0.5-0.7** | 🟠 **Moderada** | Relevante pero no perfecto | Resultado útil, revisar contexto |
| **0.3-0.5** | 🔴 **Baja** | Poco relevante para la consulta | Considerar refinar búsqueda |
| **0.0-0.3** | ⚫ **Muy Baja** | Probablemente no relevante | Resultado no recomendado |

#### Ejemplos Prácticos

**Consulta**: "configuración alertas"
```json
{
  "resultados": [
    {
      "data": {
        "Descripcion": "Configura las notificaciones y alertas del sistema"
      },
      "score": 0.8547  // 🟡 Alta similitud - Muy relevante
    },
    {
      "data": {
        "Descripcion": "Configurar parámetros generales del sistema"
      },
      "score": 0.6234  // 🟠 Moderada - Relacionado pero no específico
    },
    {
      "data": {
        "Descripcion": "Gestión de usuarios y permisos"
      },
      "score": 0.2156  // ⚫ Muy baja - No relevante
    }
  ]
}
```

#### Consejos para Optimizar Búsquedas

- **Scores > 0.7**: Resultados altamente confiables, úsalos directamente
- **Scores 0.5-0.7**: Revisa el contexto antes de usar
- **Scores < 0.5**: Considera refinar tu consulta con más palabras clave
- **Todos los scores bajos**: Intenta reformular la pregunta o usar sinónimos

### Endpoints de Sincronización

Los nuevos endpoints de sincronización permiten mantener la base de datos vectorial actualizada con las consultas guardadas de la base de datos relacional.

#### Crear o Actualizar Consulta

```bash
curl -X POST "http://localhost:8000/api/v1/consultas/upsert" \
  -H "X-API-Key: tu_clave_api" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
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
    }
  }'
```

**Respuesta:**
```json
{
  "id": 123,
  "status": "success",
  "message": "Consulta sincronizada exitosamente",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Eliminar Consulta

```bash
curl -X DELETE "http://localhost:8000/api/v1/consultas/123" \
  -H "X-API-Key: tu_clave_api"
```

**Respuesta:** `204 No Content` (exitoso) o `404 Not Found` (no existe)

#### Casos de Uso

- **Sincronización automática**: Llamar desde `savedquery_service` cuando se crea/actualiza/elimina una consulta
- **Re-indexación**: Actualizar consultas existentes con nuevos metadatos
- **Limpieza**: Eliminar consultas obsoletas de la base de datos vectorial

### Autenticación

Todas las peticiones a endpoints protegidos requieren header `X-API-Key`:

```bash
curl -H "X-API-Key: tu_clave_api" http://localhost:8000/api/v1/health
```

### Códigos de Respuesta

- `200` - Éxito (operación completada)
- `204` - No Content (eliminación exitosa)
- `400` - Petición inválida
- `401` - Autenticación requerida
- `403` - Clave API inválida
- `404` - Recurso no encontrado
- `422` - Error de validación
- `500` - Error interno del servidor
- `503` - Servicio no disponible (Qdrant o embeddings)

### Casos de Uso de Similarity Scores

#### 🎯 Filtrado por Confianza
```javascript
// Filtrar solo resultados altamente confiables
const resultadosConfiables = response.resultados.filter(r => r.score >= 0.7);

// Mostrar advertencia para scores bajos
if (resultado.score < 0.5) {
  console.warn("Resultado con baja confianza, considerar alternativas");
}
```

#### 📊 Ordenamiento Inteligente
Los resultados ya vienen ordenados por score descendente, pero puedes aplicar lógica adicional:

```javascript
// Priorizar por score y categoría
const resultadosOrdenados = response.resultados.sort((a, b) => {
  // Primero por score
  if (Math.abs(a.score - b.score) > 0.1) {
    return b.score - a.score;
  }
  // Luego por categoría preferida
  return a.data.Nivel0 === "Configuración" ? -1 : 1;
});
```

#### 🚦 Interfaz de Usuario Adaptativa
```javascript
// Mostrar indicadores visuales basados en score
function getScoreIndicator(score) {
  if (score >= 0.9) return { color: "green", text: "Excelente coincidencia" };
  if (score >= 0.7) return { color: "yellow", text: "Muy relevante" };
  if (score >= 0.5) return { color: "orange", text: "Moderadamente relevante" };
  return { color: "red", text: "Baja relevancia" };
}
```

## 🔄 Indexación

### Script de Indexación

El script `indexar.py` implementa la estrategia "scorched earth":

```bash
# Opciones disponibles
python indexar.py --help

# Indexación con archivo personalizado
python indexar.py --file data/custom.json

# Modo verbose para debugging
python indexar.py --verbose

# Dry-run para validar sin cambios
python indexar.py --dry-run
```

### Proceso de Indexación

1. **Validación** - Verifica entorno y configuración
2. **Carga** - Lee datos desde archivo JSON
3. **Validación** - Valida estructura con modelos Pydantic
4. **Eliminación** - Borra colección existente (scorched earth)
5. **Indexación** - Crea nueva colección con embeddings
6. **Verificación** - Confirma que la indexación fue exitosa

## 🐳 Docker

### Desarrollo

```bash
# Iniciar todos los servicios
docker-compose up -d

# Solo API con hot-reload
docker-compose --profile dev up -d

# Ver logs
docker-compose logs -f
```

### Producción

```bash
# Iniciar en modo producción
docker-compose -f docker-compose.prod.yml up -d

# Con Nginx reverse proxy
docker-compose -f docker-compose.prod.yml --profile nginx up -d
```

Ver [DOCKER.md](DOCKER.md) para documentación completa de Docker.

## 💻 Desarrollo

### Estructura del Proyecto

```
menu-api/
├── app/                          # Código principal
│   ├── api/                     # Endpoints de API
│   │   └── v1/                 # API versión 1
│   │       ├── router.py       # Endpoints (buscar, upsert, delete)
│   │       └── schemas.py      # Modelos Pydantic
│   ├── core/                   # Funcionalidades core
│   │   ├── exceptions.py       # Excepciones personalizadas
│   │   ├── logging.py          # Configuración de logging
│   │   └── security.py         # Autenticación y seguridad
│   ├── services/               # Servicios de negocio
│   │   ├── qdrant_service.py   # Servicio de Qdrant
│   │   ├── search_service.py   # Servicio de búsqueda
│   │   └── embedding_service.py # Servicio de embeddings
│   └── config/                 # Configuración
│       └── settings.py         # Variables de entorno (Pydantic v2)
├── tests/                      # Suite pytest (fakes: Qdrant en memoria + embeddings)
│   ├── conftest.py            # Fixtures y fakes
│   ├── test_normalizer.py
│   ├── test_menu_item.py
│   ├── test_search_service.py  # Round-trip, filtros, umbral, paginación
│   └── test_api.py            # Auth 401/403, payload completo, batch, CORS
├── data/                       # Datos y almacenamiento
│   └── qdrant_storage/        # Datos de Qdrant (Docker volume)
├── scripts/                    # Scripts de utilidad
├── docs/                       # Documentación adicional
├── .kiro/                      # Especificaciones de features
│   └── specs/                 # Specs de desarrollo
├── main.py                     # Punto de entrada
├── requirements.txt            # Dependencias Python
├── docker-compose.yml          # Configuración Docker
└── MIGRATION_CHROMADB_TO_QDRANT.md  # Guía de migración
```

### Comandos de Desarrollo

```bash
# Instalar dependencias de desarrollo
pip install pytest pytest-asyncio httpx black flake8

# Ejecutar tests
pytest

# Formatear código
black .

# Linting
flake8 .

# Servidor de desarrollo con hot-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Agregar Nueva Versión de API

1. Crear directorio `app/api/v2/`
2. Implementar `router.py` y `schemas.py`
3. Registrar en `main.py`:
   ```python
   from app.api.v2 import router as v2_router
   app.include_router(v2_router.router, prefix="/api")
   ```

## 🚀 Despliegue

### Despliegue Local

```bash
# 1. Configurar producción
cp .env.example .env.production
# Editar con valores de producción

# 2. Construir imagen
docker build -t menu-api:latest .

# 3. Ejecutar
docker run -d \
  --name menu-api \
  -p 80:8000 \
  --env-file .env.production \
  -v $(pwd)/data/chroma_db:/data/chroma_db \
  menu-api:latest
```

### Despliegue en la Nube

#### Docker Compose

```bash
# Usar configuración de producción
docker-compose -f docker-compose.prod.yml up -d
```

#### Kubernetes (ejemplo)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: menu-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: menu-api
  template:
    metadata:
      labels:
        app: menu-api
    spec:
      containers:
      - name: menu-api
        image: menu-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: MENU_API_KEY
          valueFrom:
            secretKeyRef:
              name: menu-secrets
              key: api-key
```

### Variables de Entorno de Producción

```bash
# Seguridad
MENU_API_KEY=clave_produccion_muy_segura
OPENAI_API_KEY=sk-clave_openai_real

# Configuración
LOG_LEVEL=INFO
CORS_ALLOWED_ORIGINS=https://tu-dominio-produccion.com

# Base de datos
CHROMA_DB_PATH=/data/chroma_db
```

## 🔧 Troubleshooting

### Problemas Comunes

**Error: "Incorrect API key provided"**
```bash
# Verificar clave OpenAI en .env
echo $OPENAI_API_KEY
```

**Error: "Servicio de base de datos vectorial no disponible"**
```bash
# Verificar que Qdrant esté corriendo
curl http://localhost:6333/health

# Iniciar Qdrant con Docker
docker run -p 6333:6333 qdrant/qdrant

# O con docker-compose
docker-compose up -d qdrant
```

**Error: "Collection not found"**
```bash
# La colección se crea automáticamente en el startup
# Verificar logs de la aplicación
docker-compose logs menu-api

# O reiniciar la aplicación
docker-compose restart menu-api
```

**Error: "Port already in use"**
```bash
# Cambiar puerto en .env
PORT=8001

# O detener el servicio que usa el puerto
docker-compose down
```

**Error de permisos en Docker**
```bash
# Arreglar permisos de volúmenes de Qdrant
sudo chown -R 1000:1000 ./data/qdrant_storage
```

**Error: "Query not found" (404)**
```bash
# La consulta no existe en Qdrant
# Verificar que se haya sincronizado correctamente
curl -X POST "http://localhost:8000/api/v1/consultas/upsert" \
  -H "X-API-Key: tu_clave_api" \
  -H "Content-Type: application/json" \
  -d '{"query": {...}}'
```

### Logs y Debugging

```bash
# Ver logs de la aplicación
docker-compose logs -f menu-api

# Logs con nivel DEBUG
LOG_LEVEL=DEBUG python main.py

# Health check detallado
curl http://localhost:8000/api/v1/health
```

## 🤝 Contribución

### Proceso de Contribución

1. Fork del repositorio
2. Crear rama feature: `git checkout -b feature/nueva-funcionalidad`
3. Commit cambios: `git commit -am 'Agregar nueva funcionalidad'`
4. Push a la rama: `git push origin feature/nueva-funcionalidad`
5. Crear Pull Request

### Estándares de Código

- Usar Black para formateo
- Seguir PEP 8
- Documentar funciones públicas
- Agregar tests para nueva funcionalidad
- Actualizar documentación

### Reportar Issues

Al reportar un issue, incluir:

- Versión de Python
- Comando ejecutado
- Error completo
- Logs relevantes
- Configuración (sin claves sensibles)

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver [LICENSE](LICENSE) para más detalles.

## 🙏 Agradecimientos

- [FastAPI](https://fastapi.tiangolo.com/) - Framework web moderno
- [LangChain](https://langchain.com/) - Framework para aplicaciones LLM
- [Qdrant](https://qdrant.tech/) - Base de datos vectorial
- [OpenAI](https://openai.com/) - Modelos de embeddings

## 📞 Soporte

- 📧 Email: soporte@menu-api.com
- 📖 Documentación: [/docs](http://localhost:8000/docs)
- 🐛 Issues: [GitHub Issues](https://github.com/menu-api/issues)
- 💬 Discusiones: [GitHub Discussions](https://github.com/menu-api/discussions)

---

**Versión**: 2.0.0  
**Última actualización**: Noviembre 2024  
**Cambios principales**: Migración a Qdrant, endpoints de sincronización CRUD, mejoras en health checks
##
 🚀 Optimizaciones Implementadas

### Mejoras de Búsqueda Recientes

- **✅ Normalización de Texto**: Búsquedas consistentes sin importar tildes o mayúsculas
- **✅ Formato JSON Extendido**: Soporte para sinónimos y acciones integradas  
- **✅ Compatibilidad Total**: Funciona con formato actual y extendido simultáneamente
- **✅ Rendimiento Garantizado**: Mantiene tiempos de respuesta < 2 segundos

### Ejemplos de Mejoras

```bash
# Antes: Solo coincidencias exactas
"configuración" ≠ "configuracion"

# Ahora: Normalización automática  
"configuración" = "configuracion" = "CONFIGURACIÓN"

# Antes: Solo términos del JSON original
"usuarios" → resultados limitados

# Ahora: Con sinónimos integrados
"personas" = "colaboradores" = "empleados" → encuentra "Usuarios"
```

### Documentación Completa

Ver [docs/OPTIMIZACIONES.md](docs/OPTIMIZACIONES.md) para detalles completos sobre:
- Formato JSON extendido
- Migración gradual
- Validación y pruebas
- Troubleshooting

### Comandos de Validación

```bash
# Ejecutar la suite de tests (no requiere red ni OpenAI: Qdrant en memoria + embeddings fake)
pytest -q

# Reindexar menu.json en Qdrant (requiere Qdrant + OPENAI_API_KEY)
python indexar.py --verbose --debug-text

# Validación previa sin cambios
python indexar.py --dry-run
```