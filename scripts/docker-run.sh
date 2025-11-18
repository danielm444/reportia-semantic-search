#!/bin/bash
# Script para ejecutar el contenedor Docker
# API de Búsqueda Semántica MENU

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Variables
IMAGE_NAME="menu-api"
TAG=${1:-latest}
CONTAINER_NAME="menu-api-container"
PORT=${2:-8000}

echo -e "${YELLOW}🚀 Ejecutando contenedor Docker: ${IMAGE_NAME}:${TAG}${NC}"

# Verificar que la imagen existe
if ! docker images "${IMAGE_NAME}:${TAG}" | grep -q "${TAG}"; then
    echo -e "${RED}❌ Error: Imagen no encontrada: ${IMAGE_NAME}:${TAG}${NC}"
    echo -e "${YELLOW}💡 Ejecuta primero: ./scripts/docker-build.sh${NC}"
    exit 1
fi

# Detener contenedor existente si está corriendo
if docker ps -q -f name="${CONTAINER_NAME}" | grep -q .; then
    echo -e "${YELLOW}🛑 Deteniendo contenedor existente...${NC}"
    docker stop "${CONTAINER_NAME}"
fi

# Remover contenedor existente si existe
if docker ps -aq -f name="${CONTAINER_NAME}" | grep -q .; then
    echo -e "${YELLOW}🗑️  Removiendo contenedor existente...${NC}"
    docker rm "${CONTAINER_NAME}"
fi

# Crear directorio para volumen si no existe
mkdir -p ./data/chroma_db

# Verificar que existe .env
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  Archivo .env no encontrado, copiando desde .env.example${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
    else
        echo -e "${RED}❌ Error: .env.example tampoco existe${NC}"
        exit 1
    fi
fi

# Ejecutar contenedor
echo -e "${YELLOW}🐳 Iniciando contenedor...${NC}"
docker run -d \
    --name "${CONTAINER_NAME}" \
    -p "${PORT}:8000" \
    -v "$(pwd)/data/chroma_db:/data/chroma_db" \
    -v "$(pwd)/data:/app/data:ro" \
    --env-file .env \
    --restart unless-stopped \
    "${IMAGE_NAME}:${TAG}"

# Verificar que el contenedor está corriendo
sleep 2
if docker ps -q -f name="${CONTAINER_NAME}" | grep -q .; then
    echo -e "${GREEN}✅ Contenedor iniciado exitosamente!${NC}"
    echo -e "${YELLOW}📊 Estado del contenedor:${NC}"
    docker ps -f name="${CONTAINER_NAME}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    echo -e "${YELLOW}🌐 Endpoints disponibles:${NC}"
    echo -e "  • API: http://localhost:${PORT}"
    echo -e "  • Docs: http://localhost:${PORT}/docs"
    echo -e "  • Health: http://localhost:${PORT}/health"
    
    echo -e "${YELLOW}📋 Comandos útiles:${NC}"
    echo -e "  • Ver logs: docker logs -f ${CONTAINER_NAME}"
    echo -e "  • Detener: docker stop ${CONTAINER_NAME}"
    echo -e "  • Entrar al contenedor: docker exec -it ${CONTAINER_NAME} bash"
    
else
    echo -e "${RED}❌ Error: El contenedor no se inició correctamente${NC}"
    echo -e "${YELLOW}📋 Logs del contenedor:${NC}"
    docker logs "${CONTAINER_NAME}"
    exit 1
fi