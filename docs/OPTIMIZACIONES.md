# Optimizaciones de Búsqueda Semántica

## 🚀 Resumen de Mejoras Implementadas

Este documento describe las optimizaciones implementadas para mejorar la precisión y funcionalidad de la búsqueda semántica sin comprometer el rendimiento ni la compatibilidad.

### ✅ Mejoras Implementadas

1. **Normalización de Texto**: Búsquedas consistentes independientemente de tildes y mayúsculas
2. **Formato JSON Extendido**: Soporte para sinónimos y acciones integradas
3. **Texto Canónico Optimizado**: Formato estructurado para mejor indexación
4. **Compatibilidad Total**: Funciona con formato actual y extendido simultáneamente
5. **Rendimiento Garantizado**: Mantiene tiempos de respuesta < 2 segundos

## 📊 Comparación Antes vs Después

### Antes de las Optimizaciones

```bash
# Búsquedas sensibles a tildes y mayúsculas
"configuración" ≠ "configuracion" ≠ "CONFIGURACIÓN"

# Solo términos exactos del JSON
"usuarios" → resultados limitados

# Formato rígido
Solo campos ID, Nivel0, Nivel1, Descripcion
```

### Después de las Optimizaciones

```bash
# Normalización automática
"configuración" = "configuracion" = "CONFIGURACIÓN"

# Búsqueda enriquecida con sinónimos
"personas" = "colaboradores" = "empleados" → encuentra "Usuarios"

# Formato flexible y compatible
Soporta ambos formatos + campos adicionales
```

## 🔧 Componentes Implementados

### 1. Módulo de Normalización (`app/core/text_normalizer.py`)

```python
from app.core.text_normalizer import normalize_text

# Normaliza texto eliminando tildes, convirtiendo a minúsculas
texto_normalizado = normalize_text("Configuración del SISTEMA")
# Resultado: "configuracion del sistema"
```

**Funciones disponibles:**
- `normalize_text(texto)`: Normalización completa
- `quitar_tildes(texto)`: Solo elimina tildes
- `normalize_query(consulta)`: Específica para consultas de búsqueda

### 2. Modelo MenuItem Extendido

El modelo ahora soporta campos adicionales manteniendo compatibilidad:

```python
# Formato actual (sigue funcionando)
{
  "ID": 1,
  "Nivel0": "Configuración",
  "Nivel1": "Sistema",
  "Descripcion": "Configurar parámetros del sistema"
}

# Formato extendido (nuevo)
{
  "id": 2,
  "titulo": "Usuarios › Gestión",
  "nivel": ["Usuarios", "Gestión"],
  "descripcion": "Administrar usuarios y permisos",
  "sinonimos": ["personas", "colaboradores", "empleados"],
  "acciones": ["crear", "administrar", "gestionar"],
  "texto_indexado": "Ruta del menú: Usuarios > Gestión. Descripción: Administrar usuarios y permisos."
}
```

### 3. SearchService Optimizado

- **Normalización automática** de consultas antes de buscar
- **Logging mejorado** con métricas de rendimiento
- **Validación de tiempo** de respuesta (< 2 segundos)

### 4. Script de Indexación Mejorado

```bash
# Indexación básica (solo normalización)
python indexar.py --verbose

# Indexación con debugging
python indexar.py --verbose --debug-text
```

**Nuevas características:**
- Soporte para formato mixto (actual + extendido)
- Estadísticas de compatibilidad
- Filtrado automático de metadatos complejos para ChromaDB
- Validación de rendimiento durante indexación

## 📋 Formato JSON Extendido

### Campos Nuevos Opcionales

| Campo | Tipo | Descripción | Ejemplo |
|-------|------|-------------|---------|
| `sinonimos` | `List[str]` | Términos alternativos | `["personas", "colaboradores"]` |
| `acciones` | `List[str]` | Verbos/acciones relacionadas | `["crear", "administrar"]` |
| `texto_indexado` | `str` | Texto pre-calculado para indexación | `"Ruta del menú: X > Y..."` |
| `nivel` | `List[str]` | Niveles como array | `["Usuarios", "Gestión"]` |
| `idioma` | `str` | Idioma del elemento | `"es"` |

### Migración Gradual

1. **Mantén elementos existentes** - No necesitas cambiar nada
2. **Agrega nuevos elementos** en formato optimizado
3. **Migra gradualmente** elementos importantes
4. **Sin interrupciones** - Ambos formatos funcionan simultáneamente

### Ejemplo de Migración

```json
[
  {
    "ID": 1,
    "Nivel0": "Configuración",
    "Nivel1": "Sistema", 
    "Descripcion": "Configurar parámetros generales del sistema",
    "url": "localhost/config/sistema",
    "keywords": ["configuración", "sistema"],
    "item_type": "configuration",
    "status": "active"
  },
  {
    "id": 2,
    "titulo": "Usuarios › Gestión",
    "nivel": ["Usuarios", "Gestión"],
    "descripcion": "Administrar usuarios, roles y permisos del sistema",
    "sinonimos": ["personas", "colaboradores", "empleados", "cuentas"],
    "acciones": ["crear", "administrar", "invitar", "asignar permisos", "gestionar"],
    "url": "localhost/usuarios/gestion",
    "idioma": "es",
    "estado": "active",
    "tipo": "user_management"
  }
]
```

## 🧪 Validación y Pruebas

### Probar Normalización

```bash
# Ejecutar pruebas de optimización
python test_optimization.py

# Probar API completa
python test_api_simple.py
```

### Validar Búsquedas Equivalentes

```bash
# Estas consultas deben retornar resultados idénticos:
curl -X POST "http://localhost:8000/api/v1/buscar" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: tu_clave_api" \
  -d '{"pregunta": "configuración", "top_k": 3}'

curl -X POST "http://localhost:8000/api/v1/buscar" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: tu_clave_api" \
  -d '{"pregunta": "CONFIGURACIÓN", "top_k": 3}'
```

### Validar Sinónimos

```bash
# Buscar por sinónimo debe encontrar el elemento principal
curl -X POST "http://localhost:8000/api/v1/buscar" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: tu_clave_api" \
  -d '{"pregunta": "personas", "top_k": 3}'
# Debe encontrar elementos relacionados con "Usuarios"
```

## 📈 Métricas de Rendimiento

### Logs Optimizados

Los logs ahora incluyen métricas de optimización:

```json
{
  "event": "Búsqueda con consulta normalizada",
  "original_query": "configuración",
  "normalized_query": "configuracion", 
  "query_length": 13,
  "results_found": 3,
  "response_time_seconds": 0.15,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Estadísticas de Indexación

```json
{
  "event": "Documentos LangChain creados: 5",
  "formato_actual": 1,
  "formato_extendido": 4,
  "con_texto_precalculado": 2
}
```

## 🔄 Rollback y Recuperación

### Rollback Rápido

Si necesitas volver al estado anterior:

```bash
# 1. Restaurar datos originales
cp data/menu.json.backup data/menu.json

# 2. Reindexar
python indexar.py --verbose

# 3. Reiniciar servicio
# El sistema volverá a funcionar con el formato anterior
```

### Validación Post-Rollback

```bash
# Verificar que el sistema funciona correctamente
curl -X GET "http://localhost:8000/api/v1/health"
```

## 🛠 Troubleshooting

### Problemas Comunes

1. **Error de normalización**
   ```bash
   # Probar normalización directamente
   python -c "from app.core.text_normalizer import normalize_text; print(normalize_text('Configuración'))"
   ```

2. **Formato JSON mixto**
   ```bash
   # Verificar compatibilidad
   python indexar.py --dry-run --verbose
   ```

3. **Rendimiento degradado**
   ```bash
   # Verificar tiempos de respuesta
   python test_optimization.py
   ```

### Validación de Integridad

```bash
# Verificar que todos los elementos se procesan correctamente
python -c "
from app.models.search_models import MenuItem
import json

with open('data/menu.json') as f:
    data = json.load(f)

for item in data:
    try:
        menu_item = MenuItem(**item)
        formato = 'extendido' if menu_item.is_extended_format() else 'actual'
        print(f'✅ ID {menu_item.get_effective_id()}: {formato}')
    except Exception as e:
        print(f'❌ Error: {e}')
"
```

## 📚 Recursos Adicionales

### Documentación Relacionada

- [README.md](../README.md) - Documentación principal
- [MENU_JSON_FORMAT.md](MENU_JSON_FORMAT.md) - Formato de datos detallado
- [DEPLOYMENT.md](DEPLOYMENT.md) - Guía de despliegue

### Scripts de Utilidad

- `test_optimization.py` - Pruebas de optimización
- `test_api_simple.py` - Pruebas de API
- `indexar.py` - Script de indexación mejorado

## 🎯 Próximos Pasos

### Mejoras Futuras Sugeridas

1. **Cache de consultas frecuentes** para mejorar rendimiento
2. **Análisis de sinónimos automático** basado en patrones de búsqueda
3. **Soporte multiidioma** usando el campo `idioma`
4. **Métricas de efectividad** de sinónimos y acciones

### Monitoreo Recomendado

- Tiempo de respuesta promedio
- Efectividad de sinónimos (consultas que encuentran resultados)
- Distribución de uso entre formato actual vs extendido
- Patrones de consultas más frecuentes

---

**🚀 Las optimizaciones están listas y funcionando. El sistema mantiene total compatibilidad mientras ofrece capacidades de búsqueda mejoradas.**