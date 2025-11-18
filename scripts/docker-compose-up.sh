#!/bin/bash
# Script para ejecutar con Docker Compose
# API de Búsqueda Semántica MENU

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Variables
COMPOSE_FILE=${1:-docker-compose.yml}
PROFILE=${2:-""}

echo -e "${YELLOW}🐳 Iniciando servicios con Docker Compose${NC}"
echo -e "${YELLOW}📄 Usando archivo: ${COMPOSE_FILE}${NC}"

# Verificar que existe docker-compose.yml
if [ ! -f "$COMPOSE_FILE" ]; then
    echo -e "${RED}❌ Error: Archivo no encontrado: $COMPOSE_FILE${NC}"
    exit 1
fi

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

# Crear directorios necesarios
mkdir -p ./data/chroma_db ./logs

# Construir imágenes si es necesario
echo -e "${YELLOW}🔨 Construyendo imágenes...${NC}"
if [ -n "$PROFILE" ]; then
    docker-compose -f "$COMPOSE_FILE" --profile "$PROFILE" build
else
    docker-compose -f "$COMPOSE_FILE" build
fi

# Iniciar servicios
echo -e "${YELLOW}🚀 Iniciando servicios...${NC}"
if [ -n "$PROFILE" ]; then
    docker-compose -f "$COMPOSE_FILE" --profile "$PROFILE" up -d
else
    docker-compose -f "$COMPOSE_FILE" up -d
fi

# Verificar estado de los servicios
sleep 5
echo -e "${YELLOW}📊 Estado de los servicios:${NC}"
docker-compose -f "$COMPOSE_FILE" ps

# Mostrar logs del indexer (si existe)
if docker-compose -f "$COMPOSE_FILE" ps | grep -q "menu-indexer"; then
    echo -e "${YELLOW}📋 Logs del indexer:${NC}"
    docker-compose -f "$COMPOSE_FILE" logs menu-indexer
fi

# Información útil
echo -e "${GREEN}✅ Servicios iniciados exitosamente!${NC}"
echo -e "${YELLOW}🌐 Endpoints disponibles:${NC}"
echo -e "  • API: http://localhost:8000"
echo -e "  • Docs: http://localhost:8000/docs"
echo -e "  • Health: http://localhost:8000/health"

if [ "$PROFILE" = "dev" ]; then
    echo -e "  • API Dev (hot-reload): http://localhost:8001"
fi

echo -e "${YELLOW}📋 Comandos útiles:${NC}"
echo -e "  • Ver logs: docker-compose -f $COMPOSE_FILE logs -f"
echo -e "  • Detener: docker-compose -f $COMPOSE_FILE down"
echo -e "  • Reiniciar: docker-compose -f $COMPOSE_FILE restart"
echo -e "  • Ver estado: docker-compose -f $COMPOSE_FILE ps"