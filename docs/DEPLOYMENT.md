# Guía de Despliegue - API de Búsqueda Semántica MENU

Esta guía detalla los diferentes métodos de despliegue para la API de Búsqueda Semántica MENU en diversos entornos.

## 📋 Tabla de Contenidos

- [Requisitos Previos](#-requisitos-previos)
- [Despliegue Local](#-despliegue-local)
- [Despliegue con Docker](#-despliegue-con-docker)
- [Despliegue en la Nube](#-despliegue-en-la-nube)
- [Configuración de Producción](#-configuración-de-producción)
- [Monitoreo y Mantenimiento](#-monitoreo-y-mantenimiento)
- [Troubleshooting](#-troubleshooting)

## 🔧 Requisitos Previos

### Requisitos del Sistema

- **CPU**: 2+ cores (recomendado 4+ para producción)
- **RAM**: 4GB mínimo (8GB+ recomendado para producción)
- **Almacenamiento**: 10GB+ espacio libre
- **Red**: Acceso a internet para OpenAI API

### Software Requerido

- **Python**: 3.11 o superior
- **Docker**: 20.10+ (opcional pero recomendado)
- **Docker Compose**: 2.0+ (para orquestación)
- **Git**: Para clonar el repositorio

### Claves y Credenciales

- **OpenAI API Key**: Obtener en [OpenAI Platform](https://platform.openai.com/account/api-keys)
- **Dominio**: Para despliegue en producción (opcional)
- **Certificados SSL**: Para HTTPS (recomendado en producción)

## 🏠 Despliegue Local

### Método 1: Instalación Directa

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

# 5. Indexar datos iniciales
python indexar.py

# 6. Iniciar servidor
python main.py
```

### Método 2: Servidor de Producción Local

```bash
# Usar Gunicorn para mejor rendimiento
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app -b 0.0.0.0:8000

# Con configuración avanzada
gunicorn \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile - \
  --log-level info \
  main:app
```

### Verificación Local

```bash
# Health check
curl http://localhost:8000/health

# Test de búsqueda
curl -X POST "http://localhost:8000/api/v1/buscar" \
  -H "X-API-Key: tu_clave_api" \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "configuración", "top_k": 3}'
```

## 🐳 Despliegue con Docker

### Desarrollo

```bash
# 1. Configurar entorno
cp .env.example .env
# Editar .env con tus claves

# 2. Iniciar servicios
docker-compose up -d

# 3. Ver logs
docker-compose logs -f

# 4. Verificar estado
docker-compose ps
```

### Producción

```bash
# 1. Configurar producción
cp .env.example .env.production
# Configurar con valores de producción

# 2. Iniciar en modo producción
docker-compose -f docker-compose.prod.yml up -d

# 3. Verificar despliegue
curl http://localhost/health
```

### Build Personalizado

```bash
# Construir imagen personalizada
docker build -t menu-api:custom .

# Ejecutar con configuración específica
docker run -d \
  --name menu-api-prod \
  -p 80:8000 \
  -v $(pwd)/data/chroma_db:/data/chroma_db \
  -v $(pwd)/logs:/app/logs \
  --env-file .env.production \
  --restart unless-stopped \
  menu-api:custom
```

## ☁️ Despliegue en la Nube

### AWS EC2

#### 1. Preparar Instancia

```bash
# Conectar a instancia EC2
ssh -i key.pem ubuntu@ec2-instance-ip

# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### 2. Desplegar Aplicación

```bash
# Clonar repositorio
git clone <repository-url>
cd menu-api

# Configurar producción
cp .env.example .env
# Editar con valores de producción

# Iniciar servicios
docker-compose -f docker-compose.prod.yml up -d

# Configurar nginx (opcional)
sudo apt install nginx
sudo cp nginx/nginx.conf /etc/nginx/sites-available/menu-api
sudo ln -s /etc/nginx/sites-available/menu-api /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

#### 3. Configurar Dominio y SSL

```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx

# Obtener certificado SSL
sudo certbot --nginx -d tu-dominio.com

# Verificar renovación automática
sudo certbot renew --dry-run
```

### Google Cloud Platform

#### 1. Cloud Run

```bash
# Construir y subir imagen
gcloud builds submit --tag gcr.io/PROJECT-ID/menu-api

# Desplegar en Cloud Run
gcloud run deploy menu-api \
  --image gcr.io/PROJECT-ID/menu-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars MENU_API_KEY=tu_clave,OPENAI_API_KEY=tu_openai_key
```

#### 2. Compute Engine

```bash
# Crear instancia
gcloud compute instances create menu-api-instance \
  --image-family ubuntu-2004-lts \
  --image-project ubuntu-os-cloud \
  --machine-type e2-medium \
  --zone us-central1-a

# SSH y configurar como EC2
gcloud compute ssh menu-api-instance --zone us-central1-a
```

### Azure Container Instances

```bash
# Crear grupo de recursos
az group create --name menu-api-rg --location eastus

# Desplegar contenedor
az container create \
  --resource-group menu-api-rg \
  --name menu-api \
  --image menu-api:latest \
  --dns-name-label menu-api-unique \
  --ports 8000 \
  --environment-variables \
    MENU_API_KEY=tu_clave \
    OPENAI_API_KEY=tu_openai_key
```

### DigitalOcean Droplet

```bash
# Crear droplet con Docker pre-instalado
doctl compute droplet create menu-api \
  --image docker-20-04 \
  --size s-2vcpu-4gb \
  --region nyc1

# SSH y desplegar
ssh root@droplet-ip
git clone <repository-url>
cd menu-api
docker-compose -f docker-compose.prod.yml up -d
```

## ⚙️ Configuración de Producción

### Variables de Entorno

```bash
# .env.production
MENU_API_KEY=clave_produccion_muy_segura
OPENAI_API_KEY=sk-clave_openai_real
LOG_LEVEL=INFO
CORS_ALLOWED_ORIGINS=https://tu-dominio.com
CHROMA_DB_PATH=/data/chroma_db
HOST=0.0.0.0
PORT=8000
```

### Nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/menu-api
server {
    listen 80;
    server_name tu-dominio.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Systemd Service (Alternativa a Docker)

```ini
# /etc/systemd/system/menu-api.service
[Unit]
Description=Menu API Service
After=network.target

[Service]
Type=exec
User=menuapi
Group=menuapi
WorkingDirectory=/opt/menu-api
Environment=PATH=/opt/menu-api/venv/bin
EnvironmentFile=/opt/menu-api/.env
ExecStart=/opt/menu-api/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app -b 0.0.0.0:8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Habilitar y iniciar servicio
sudo systemctl enable menu-api
sudo systemctl start menu-api
sudo systemctl status menu-api
```

## 📊 Monitoreo y Mantenimiento

### Health Checks

```bash
# Script de monitoreo básico
#!/bin/bash
# monitor.sh

URL="http://localhost:8000/health"
EXPECTED="healthy"

response=$(curl -s $URL | jq -r '.status')

if [ "$response" = "$EXPECTED" ]; then
    echo "✅ Service is healthy"
    exit 0
else
    echo "❌ Service is unhealthy: $response"
    exit 1
fi
```

### Logs

```bash
# Ver logs en tiempo real
docker-compose logs -f menu-api

# Logs con filtro
docker-compose logs menu-api | grep ERROR

# Rotar logs (logrotate)
sudo nano /etc/logrotate.d/menu-api
```

### Backup

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/menu-api"

# Backup de base de datos vectorial
tar -czf "$BACKUP_DIR/chroma_db_$DATE.tar.gz" data/chroma_db/

# Backup de configuración
cp .env "$BACKUP_DIR/env_$DATE.backup"

# Limpiar backups antiguos (más de 30 días)
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

### Actualizaciones

```bash
#!/bin/bash
# update.sh

# Backup antes de actualizar
./backup.sh

# Actualizar código
git pull origin main

# Reconstruir imagen
docker-compose build

# Reiniciar servicios
docker-compose down
docker-compose up -d

# Verificar salud
sleep 30
curl -f http://localhost/health || echo "❌ Update failed"
```

## 🔒 Seguridad en Producción

### Firewall

```bash
# UFW (Ubuntu)
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable

# Bloquear acceso directo al puerto de la app
sudo ufw deny 8000
```

### SSL/TLS

```bash
# Let's Encrypt con Certbot
sudo certbot --nginx -d tu-dominio.com

# Verificar configuración SSL
curl -I https://tu-dominio.com
```

### Secrets Management

```bash
# Usar Docker secrets
echo "tu_clave_secreta" | docker secret create menu_api_key -

# En docker-compose.yml
secrets:
  menu_api_key:
    external: true
```

## 🚨 Troubleshooting

### Problemas Comunes

#### 1. Servicio no inicia

```bash
# Verificar logs
docker-compose logs menu-api

# Verificar configuración
docker-compose config

# Verificar puertos
netstat -tlnp | grep 8000
```

#### 2. Error de conexión OpenAI

```bash
# Verificar clave API
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models

# Verificar conectividad
ping api.openai.com
```

#### 3. Base de datos corrupta

```bash
# Backup actual
cp -r data/chroma_db data/chroma_db.backup

# Re-indexar
python indexar.py --file data/menu.json
```

#### 4. Alto uso de memoria

```bash
# Verificar uso de recursos
docker stats

# Reducir workers
# En docker-compose.yml o comando gunicorn
--workers 2
```

### Comandos de Diagnóstico

```bash
# Estado general del sistema
docker-compose ps
docker-compose logs --tail=50 menu-api

# Uso de recursos
docker stats menu-api

# Conectividad
curl -I http://localhost:8000/health

# Verificar configuración
python -c "from app.config.settings import settings; print(settings.dict())"
```

## 📈 Escalabilidad

### Escalado Horizontal

```yaml
# docker-compose.prod.yml
services:
  menu-api:
    deploy:
      replicas: 3
    
  nginx:
    depends_on:
      - menu-api
```

### Load Balancer

```nginx
upstream menu_api {
    server menu-api-1:8000;
    server menu-api-2:8000;
    server menu-api-3:8000;
}

server {
    location / {
        proxy_pass http://menu_api;
    }
}
```

### Auto-scaling (Kubernetes)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: menu-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: menu-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

Para más información sobre configuración específica, consultar:
- [README.md](../README.md) - Documentación general
- [DOCKER.md](../DOCKER.md) - Guía completa de Docker
- [MENU_JSON_FORMAT.md](MENU_JSON_FORMAT.md) - Formato de datos