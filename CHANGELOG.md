# Changelog

Todos los cambios notables de este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Sin Publicar]

### Agregado
- Preparación para futuras características

### Cambiado
- Mejoras menores en documentación

### Corregido
- Correcciones menores de bugs

## [1.0.0] - 2024-10-22

### Agregado

#### Core Features
- **API de Búsqueda Semántica**: Endpoint POST `/api/v1/buscar` para consultas en lenguaje natural
- **Autenticación por API Key**: Seguridad mediante header `X-API-Key`
- **Versionado de API**: Estructura `/api/v1` con preparación para futuras versiones
- **Documentación OpenAPI**: Swagger UI automático en `/docs`

#### Arquitectura y Abstracciones
- **Integración LangChain**: Abstracciones para embeddings y bases de datos vectoriales
- **Soporte OpenAI**: Modelo `text-embedding-3-small` para embeddings
- **ChromaDB**: Base de datos vectorial con persistencia
- **Modularidad**: Fácil intercambio de proveedores (OpenAI ↔ Cohere, ChromaDB ↔ Qdrant)

#### Indexación y Datos
- **Script de Indexación**: `indexar.py` independiente con estrategia "scorched earth"
- **Validación de Datos**: Modelos Pydantic para estructura de `menu.json`
- **Procesamiento Batch**: Indexación semanal con logging detallado
- **Formato JSON**: Estructura flexible para catálogos de datos

#### Seguridad y Middleware
- **CORS Configurable**: Orígenes permitidos desde variables de entorno
- **Headers de Seguridad**: X-Frame-Options, X-Content-Type-Options, etc.
- **Logging Estructurado**: Logs JSON con structlog
- **Manejo de Errores**: Respuestas HTTP estructuradas (401, 403, 422, 503)
- **Sanitización**: Filtrado automático de datos sensibles en logs

#### Containerización
- **Docker Multi-etapa**: Dockerfile optimizado para producción
- **Docker Compose**: Orquestación para desarrollo y producción
- **Health Checks**: Verificación automática de estado de servicios
- **Volúmenes Persistentes**: Datos de ChromaDB preservados entre reinicios
- **Nginx Integration**: Reverse proxy con rate limiting y SSL

#### Configuración y Despliegue
- **Variables de Entorno**: Configuración 12-factor app completa
- **Múltiples Entornos**: Desarrollo, testing y producción
- **Scripts de Utilidad**: Build, run y validación automatizados
- **Gunicorn + Uvicorn**: Servidor de producción con workers asíncronos

#### Documentación
- **README Completo**: Guía de instalación, uso y despliegue
- **Documentación Docker**: Guía específica para containerización
- **Formato de Datos**: Especificación detallada de `menu.json`
- **Guía de Despliegue**: Instrucciones para múltiples plataformas cloud

### Endpoints Implementados

#### Públicos
- `GET /` - Información general de la API
- `GET /health` - Health check básico
- `GET /versions` - Información de versiones disponibles
- `GET /docs` - Documentación interactiva Swagger UI
- `GET /openapi.json` - Especificación OpenAPI 3.0+

#### API v1 (Autenticados)
- `POST /api/v1/buscar` - Búsqueda semántica principal
- `GET /api/v1/health` - Health check detallado con estado de servicios
- `GET /api/v1/info` - Información y capacidades de API v1

### Tecnologías Utilizadas

#### Backend
- **FastAPI 0.104+**: Framework web moderno y rápido
- **Python 3.11+**: Lenguaje de programación principal
- **Pydantic 2.5+**: Validación de datos y serialización
- **Uvicorn**: Servidor ASGI de alto rendimiento

#### AI/ML Stack
- **LangChain 0.0.350+**: Framework para aplicaciones LLM
- **OpenAI API**: Embeddings con `text-embedding-3-small`
- **ChromaDB 0.4.18+**: Base de datos vectorial
- **Structlog**: Logging estructurado en JSON

#### DevOps y Deployment
- **Docker**: Containerización con multi-stage builds
- **Docker Compose**: Orquestación de servicios
- **Gunicorn**: Servidor WSGI/ASGI para producción
- **Nginx**: Reverse proxy y load balancer

### Configuración

#### Variables de Entorno Soportadas
```bash
# API Configuration
MENU_API_KEY=tu_clave_secreta
CORS_ALLOWED_ORIGINS=https://app.dominio.com

# OpenAI Configuration
OPENAI_API_KEY=sk-tu_clave_openai

# Database Configuration
CHROMA_DB_PATH=./data/chroma_db

# Server Configuration
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
```

#### Archivos de Configuración
- `.env.example` - Plantilla de configuración para desarrollo
- `.env.production.example` - Plantilla optimizada para producción
- `docker-compose.yml` - Configuración de desarrollo
- `docker-compose.prod.yml` - Configuración de producción

### Estructura del Proyecto

```
menu-api/
├── app/                    # Código principal de la aplicación
│   ├── api/v1/            # Endpoints de API versión 1
│   ├── core/              # Funcionalidades core (seguridad, logging)
│   ├── services/          # Servicios de negocio (embeddings, búsqueda)
│   ├── models/            # Modelos de datos Pydantic
│   └── config/            # Configuración y settings
├── data/                  # Datos y base de datos vectorial
├── docs/                  # Documentación adicional
├── scripts/               # Scripts de utilidad y deployment
├── nginx/                 # Configuración de Nginx
├── indexar.py            # Script de indexación independiente
├── main.py               # Punto de entrada de la aplicación
└── requirements.txt      # Dependencias Python
```

### Características de Seguridad

- **Autenticación**: API Key obligatoria para endpoints protegidos
- **CORS**: Configuración restrictiva para orígenes permitidos
- **Headers de Seguridad**: Protección contra XSS, clickjacking, etc.
- **Logging Seguro**: Filtrado automático de datos sensibles
- **Validación de Entrada**: Sanitización y límites de tamaño
- **Usuario No-Root**: Contenedores ejecutan con usuario limitado

### Rendimiento y Escalabilidad

- **Arquitectura Asíncrona**: FastAPI + Uvicorn para alta concurrencia
- **Workers Múltiples**: Gunicorn con workers configurables
- **Caching**: Headers de cache para recursos estáticos
- **Compresión**: Gzip habilitado para respuestas
- **Health Checks**: Monitoreo automático de servicios

### Compatibilidad

- **Python**: 3.11+
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Sistemas Operativos**: Linux, macOS, Windows
- **Arquitecturas**: x86_64, ARM64

### Limitaciones Conocidas

- **Dependencia OpenAI**: Requiere conectividad a internet y clave API válida
- **Idioma Principal**: Optimizado para español, soporte limitado para otros idiomas
- **Escalado Vertical**: ChromaDB local no soporta clustering nativo
- **Persistencia**: Datos almacenados localmente, requiere backups manuales

### Migración y Compatibilidad

- **Versión Inicial**: No hay versiones anteriores
- **API Versionada**: Preparada para futuras versiones sin breaking changes
- **Datos**: Formato JSON estable y extensible
- **Configuración**: Variables de entorno retrocompatibles

---

## Formato de Versiones

Este proyecto usa [Semantic Versioning](https://semver.org/):

- **MAJOR**: Cambios incompatibles en la API
- **MINOR**: Nueva funcionalidad compatible hacia atrás
- **PATCH**: Correcciones de bugs compatibles

## Tipos de Cambios

- **Agregado**: Para nuevas características
- **Cambiado**: Para cambios en funcionalidad existente
- **Deprecado**: Para características que serán removidas
- **Removido**: Para características removidas
- **Corregido**: Para corrección de bugs
- **Seguridad**: Para vulnerabilidades de seguridad