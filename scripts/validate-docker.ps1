# Script PowerShell para validar la configuración Docker
# API de Búsqueda Semántica MENU

Write-Host "🔍 Validando configuración Docker..." -ForegroundColor Yellow

$errors = 0

# Función para verificar archivos
function Check-File {
    param($FilePath)
    if (Test-Path $FilePath) {
        Write-Host "✅ $FilePath" -ForegroundColor Green
        return $true
    } else {
        Write-Host "❌ $FilePath (no encontrado)" -ForegroundColor Red
        return $false
    }
}

# Función para verificar directorios
function Check-Directory {
    param($DirPath)
    if (Test-Path $DirPath -PathType Container) {
        Write-Host "✅ $DirPath/" -ForegroundColor Green
        return $true
    } else {
        Write-Host "❌ $DirPath/ (no encontrado)" -ForegroundColor Red
        return $false
    }
}

Write-Host "📄 Verificando archivos Docker..." -ForegroundColor Yellow
if (!(Check-File "Dockerfile")) { $errors++ }
if (!(Check-File "Dockerfile.dev")) { $errors++ }
if (!(Check-File "docker-compose.yml")) { $errors++ }
if (!(Check-File "docker-compose.prod.yml")) { $errors++ }
if (!(Check-File ".dockerignore")) { $errors++ }

Write-Host "📁 Verificando directorios..." -ForegroundColor Yellow
if (!(Check-Directory "scripts")) { $errors++ }
if (!(Check-Directory "nginx")) { $errors++ }
if (!(Check-Directory "data")) { $errors++ }

Write-Host "⚙️ Verificando archivos de configuración..." -ForegroundColor Yellow
if (!(Check-File "requirements.txt")) { $errors++ }
if (!(Check-File ".env.example")) { $errors++ }
if (!(Check-File "main.py")) { $errors++ }
if (!(Check-File "indexar.py")) { $errors++ }

# Verificar .env
if (Test-Path ".env") {
    Write-Host "✅ .env" -ForegroundColor Green
} else {
    Write-Host "⚠️ .env (no encontrado, se usará .env.example)" -ForegroundColor Yellow
}

Write-Host "🐳 Verificando Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>$null
    if ($dockerVersion) {
        Write-Host "✅ Docker instalado" -ForegroundColor Green
        Write-Host $dockerVersion
    } else {
        Write-Host "❌ Docker no instalado" -ForegroundColor Red
        $errors++
    }
} catch {
    Write-Host "❌ Docker no instalado" -ForegroundColor Red
    $errors++
}

try {
    $composeVersion = docker-compose --version 2>$null
    if ($composeVersion) {
        Write-Host "✅ Docker Compose instalado" -ForegroundColor Green
        Write-Host $composeVersion
    } else {
        Write-Host "❌ Docker Compose no instalado" -ForegroundColor Red
        $errors++
    }
} catch {
    Write-Host "❌ Docker Compose no instalado" -ForegroundColor Red
    $errors++
}

Write-Host "🔧 Verificando estructura de proyecto..." -ForegroundColor Yellow

$requiredDirs = @("app", "app/api", "app/api/v1", "app/core", "app/services", "app/models", "app/config")
foreach ($dir in $requiredDirs) {
    if (!(Check-Directory $dir)) { $errors++ }
}

$requiredFiles = @("app/__init__.py", "app/api/v1/router.py", "app/core/security.py", "app/services/search_service.py")
foreach ($file in $requiredFiles) {
    if (!(Check-File $file)) { $errors++ }
}

Write-Host "📊 Resumen de validación:" -ForegroundColor Yellow

if ($errors -eq 0) {
    Write-Host "🎉 ¡Configuración Docker válida!" -ForegroundColor Green
    Write-Host "💡 Comandos para empezar:" -ForegroundColor Yellow
    Write-Host "  • docker-compose up -d"
    Write-Host "  • docker build -t menu-api:latest ."
    Write-Host "  • docker run -p 8000:8000 menu-api:latest"
    exit 0
} else {
    Write-Host "❌ Se encontraron $errors errores" -ForegroundColor Red
    Write-Host "💡 Revisa los archivos marcados con ❌" -ForegroundColor Yellow
    exit 1
}