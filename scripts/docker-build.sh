#!/bin/bash
# Script para construir la imagen Docker de producción
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
DOCKERFILE=${2:-Dockerfile}

echo -e "${YELLOW}🐳 Construyendo imagen Docker: ${IMAGE_NAME}:${TAG}${NC}"
echo -e "${YELLOW}📄 Usando Dockerfile: ${DOCKERFILE}${NC}"

# Verificar que existe el Dockerfile
if [ ! -f "$DOCKERFILE" ]; then
    echo -e "${RED}❌ Error: Dockerfile no encontrado: $DOCKERFILE${NC}"
    exit 1
fi

# Verificar que existe requirements.txt
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ Error: requirements.txt no encontrado${NC}"
    exit 1
fi

# Construir imagen
echo -e "${YELLOW}🔨 Iniciando build...${NC}"
docker build -f "$DOCKERFILE" -t "${IMAGE_NAME}:${TAG}" .

# Verificar que la imagen se construyó correctamente
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Imagen construida exitosamente: ${IMAGE_NAME}:${TAG}${NC}"
    
    # Mostrar información de la imagen
    echo -e "${YELLOW}📊 Información de la imagen:${NC}"
    docker images "${IMAGE_NAME}:${TAG}" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
    
    # Mostrar layers (opcional)
    echo -e "${YELLOW}📋 Layers de la imagen:${NC}"
    docker history "${IMAGE_NAME}:${TAG}" --format "table {{.CreatedBy}}\t{{.Size}}"
    
else
    echo -e "${RED}❌ Error construyendo la imagen${NC}"
    exit 1
fi

echo -e "${GREEN}🎉 Build completado!${NC}"
echo -e "${YELLOW}💡 Para ejecutar: docker run -p 8000:8000 ${IMAGE_NAME}:${TAG}${NC}"