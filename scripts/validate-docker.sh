#!/bin/bash
# Script para validar la configuración Docker
# API de Búsqueda Semántica MENU

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🔍 Validando configuración Docker...${NC}"

# Función para verificar archivos
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✅ $1${NC}"
        return 0
    else
        echo -e "${RED}❌ $1 (no encontrado)${NC}"
        return 1
    fi
}

# Función para verificar directorios
check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✅ $1/${NC}"
        return 0
    else
        echo -e "${RED}❌ $1/ (no encontrado)${NC}"
        return 1
    fi
}

# Contador de errores
errors=0

echo -e "${YELLOW}📄 Verificando archivos Docker...${NC}"
check_file "Dockerfile" || ((errors++))
check_file "Dockerfile.dev" || ((errors++))
check_file "docker-compose.yml" || ((errors++))
check_file "docker-compose.prod.yml" || ((errors++))
check_file ".dockerignore" || ((errors++))

echo -e "${YELLOW}📁 Verificando directorios...${NC}"
check_dir "scripts" || ((errors++))
check_dir "nginx" || ((errors++))
check_dir "data" || ((errors++))

echo -e "${YELLOW}⚙️  Verificando archivos de configuración...${NC}"
check_file "requirements.txt" || ((errors++))
check_file ".env.example" || ((errors++))
check_file "main.py" || ((errors++))
check_file "indexar.py" || ((errors++))

# Verificar .env
if [ -f ".env" ]; then
    echo -e "${GREEN}✅ .env${NC}"
else
    echo -e "${YELLOW}⚠️  .env (no encontrado, se usará .env.example)${NC}"
fi

echo -e "${YELLOW}🐳 Verificando Docker...${NC}"
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✅ Docker instalado${NC}"
    docker --version
    
    # Verificar que Docker esté corriendo
    if docker info &> /dev/null; then
        echo -e "${GREEN}✅ Docker daemon corriendo${NC}"
    else
        echo -e "${YELLOW}⚠️  Docker daemon no está corriendo${NC}"
    fi
else
    echo -e "${RED}❌ Docker no instalado${NC}"
    ((errors++))
fi

if command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}✅ Docker Compose instalado${NC}"
    docker-compose --version
else
    echo -e "${RED}❌ Docker Compose no instalado${NC}"
    ((errors++))
fi

echo -e "${YELLOW}📋 Verificando sintaxis de archivos Docker...${NC}"

# Validar Dockerfile
if [ -f "Dockerfile" ]; then
    if docker build -f Dockerfile --dry-run . &> /dev/null 2>&1; then
        echo -e "${GREEN}✅ Dockerfile sintaxis válida${NC}"
    else
        echo -e "${YELLOW}⚠️  No se pudo validar Dockerfile (Docker daemon requerido)${NC}"
    fi
fi

# Validar docker-compose.yml
if [ -f "docker-compose.yml" ]; then
    if docker-compose -f docker-compose.yml config &> /dev/null; then
        echo -e "${GREEN}✅ docker-compose.yml sintaxis válida${NC}"
    else
        echo -e "${RED}❌ docker-compose.yml sintaxis inválida${NC}"
        ((errors++))
    fi
fi

echo -e "${YELLOW}🔧 Verificando estructura de proyecto...${NC}"

# Verificar estructura de app/
required_dirs=("app" "app/api" "app/api/v1" "app/core" "app/services" "app/models" "app/config")
for dir in "${required_dirs[@]}"; do
    check_dir "$dir" || ((errors++))
done

# Verificar archivos Python principales
required_files=("app/__init__.py" "app/api/v1/router.py" "app/core/security.py" "app/services/search_service.py")
for file in "${required_files[@]}"; do
    check_file "$file" || ((errors++))
done

echo -e "${YELLOW}📊 Resumen de validación:${NC}"

if [ $errors -eq 0 ]; then
    echo -e "${GREEN}🎉 ¡Configuración Docker válida!${NC}"
    echo -e "${YELLOW}💡 Comandos para empezar:${NC}"
    echo -e "  • docker-compose up -d"
    echo -e "  • ./scripts/docker-build.sh"
    echo -e "  • ./scripts/docker-run.sh"
    exit 0
else
    echo -e "${RED}❌ Se encontraron $errors errores${NC}"
    echo -e "${YELLOW}💡 Revisa los archivos marcados con ❌${NC}"
    exit 1
fi