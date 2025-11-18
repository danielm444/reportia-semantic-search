# Docker - API de Búsqueda Semántica MENU

Esta guía explica cómo usar Docker para ejecutar la API de Búsqueda Semántica MENU.

## 🐳 Archivos Docker

- `Dockerfile` - Imagen multi-etapa para producción
- `Dockerfile.dev` - Imagen para desarrollo con hot-reload
- `docker-compose.yml` - Orquestación para desarrollo
- `docker-compose.prod.yml` - Configuración para producción
- `.dockerignore` - Archivos excluidos del contexto Docker

## 🚀 Inicio Rápido

### Opción 1: Docker Compose (Recomendado)

```bash
# 1. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus claves reales

# 2. Iniciar servicios
docker-compose up -d

# 3. Ver logs
docker-compose logs -f

# 4. Acceder a la API
curl http://localhost:8000/health
```

### Opción 2: Docker Build Manual

```bash
# 1. Construir imagen
docker build -t menu-api:latest .

# 2. Ejecutar contenedor
docker run -d \
  --name menu-api \
  -p 8000:8000 \
  -v $(pwd)/data/chroma_db:/data/chroma_db \
  --env-file .env \
  menu-api:latest
```

## 📋 Comandos Útiles

### Desarrollo

```bash
# Desarrollo con hot-reload
docker-compose --profile dev up -d

# Reconstruir imágenes
docker-compose build

# Ver logs en tiempo real
docker-compose logs -f menu-api

# Ejecutar indexación
docker-compose run --rm menu-indexer

# Acceder al contenedor
docker-compose exec menu-api bash
```

### Producción

```bash
# Iniciar en producción
docker-compose -f docker-compose.prod.yml up -d

# Escalar servicios
docker-compose -f docker-compose.prod.yml up -d --scale menu-api=3

# Actualizar imagen
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

### Mantenimiento

```bash
# Detener servicios
docker-compose down

# Limpiar volúmenes (¡CUIDADO!)
docker-compose down -v

# Ver estado de servicios
docker-compose ps

# Ver uso de recursos
docker stats

# Limpiar imágenes no usadas
docker image prune -f
```

## 🔧 Configuración

### Variables de Entorno

Crear archivo `.env` basado en `.env.example`:

```bash
# API Configuration
MENU_API_KEY=tu_clave_secreta_aqui
CORS_ALLOWED_ORIGINS=https://tu-dominio.com

# OpenAI Configuration  
OPENAI_API_KEY=sk-tu_clave_openai_real

# Database Configuration
CHROMA_DB_PATH=/data/chroma_db

# Logging Configuration
LOG_LEVEL=INFO
```

### Volúmenes Persistentes

- `/data/chroma_db` - Base de datos vectorial (PERSISTENTE)
- `/app/logs` - Logs de la aplicación
- `/app/data` - Datos de entrada (solo lectura)

### Puertos

- `8000` - API principal
- `8001` - API desarrollo (con --profile dev)
- `80/443` - Nginx (con --profile nginx)

## 🏥 Health Checks

La imagen incluye health checks automáticos:

```bash
# Verificar salud del contenedor
docker inspect --format='{{.State.Health.Status}}' menu-api

# Health check manual
curl -f http://localhost:8000/health
```

## 🔒 Seguridad

### Buenas Prácticas Implementadas

- ✅ Usuario no-root en contenedor
- ✅ Imagen multi-etapa (imagen final slim)
- ✅ Variables de entorno para secrets
- ✅ Health checks configurados
- ✅ Límites de recursos en producción
- ✅ Reinicio automático

### Configuración Adicional

```bash
# Ejecutar con usuario específico
docker run --user 1000:1000 menu-api:latest

# Limitar recursos
docker run --memory=1g --cpus=1.0 menu-api:latest

# Solo lectura del filesystem
docker run --read-only --tmpfs /tmp menu-api:latest
```

## 🐛 Troubleshooting

### Problemas Comunes

1. **Error de permisos en volúmenes**
   ```bash
   sudo chown -R 1000:1000 ./data/chroma_db
   ```

2. **Contenedor no inicia**
   ```bash
   docker logs menu-api
   docker-compose logs menu-api
   ```

3. **Puerto ya en uso**
   ```bash
   # Cambiar puerto en docker-compose.yml
   ports:
     - "8001:8000"  # Puerto local diferente
   ```

4. **Variables de entorno no cargadas**
   ```bash
   # Verificar archivo .env
   docker-compose config
   ```

### Logs y Debugging

```bash
# Logs detallados
docker-compose logs --tail=100 -f menu-api

# Entrar al contenedor para debug
docker-compose exec menu-api bash

# Verificar configuración
docker-compose exec menu-api python -c "from app.config.settings import settings; print(settings.dict())"

# Test de conectividad
docker-compose exec menu-api curl -f http://localhost:8000/health
```

## 📊 Monitoreo

### Métricas Básicas

```bash
# Uso de recursos
docker stats menu-api

# Información del contenedor
docker inspect menu-api

# Logs con timestamps
docker-compose logs -t menu-api
```

### Integración con Monitoring

El contenedor expone métricas en:
- `/health` - Health check básico
- `/api/v1/health` - Health check detallado

## 🚀 Despliegue

### CI/CD Pipeline Ejemplo

```yaml
# .github/workflows/docker.yml
name: Docker Build and Deploy

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Build Docker image
        run: docker build -t menu-api:${{ github.sha }} .
        
      - name: Run tests
        run: docker run --rm menu-api:${{ github.sha }} python -m pytest
        
      - name: Deploy to production
        run: |
          docker tag menu-api:${{ github.sha }} menu-api:latest
          # Deploy commands here
```

## 📚 Referencias

- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [FastAPI Docker Guide](https://fastapi.tiangolo.com/deployment/docker/)