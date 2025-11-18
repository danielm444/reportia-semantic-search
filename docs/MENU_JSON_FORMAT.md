# Formato del Archivo menu.json

Esta documentación describe la estructura y formato del archivo `menu.json` que utiliza la API de Búsqueda Semántica MENU para indexar datos.

## 📋 Estructura General

El archivo `menu.json` debe contener un array JSON con objetos que representen elementos del menú o catálogo:

```json
[
  {
    "ID": 1,
    "Nivel0": "Categoría Principal",
    "Nivel1": "Subcategoría",
    "Descripcion": "Descripción del elemento",
    "url": "ruta/al/elemento"
  }
]
```

## 🔧 Campos del Schema

### Campos Obligatorios

#### `ID` (integer)
- **Descripción**: Identificador único del elemento
- **Tipo**: Número entero
- **Restricciones**: Debe ser único, mayor que 0
- **Ejemplo**: `1`, `2`, `100`

```json
{
  "ID": 1
}
```

#### `Nivel0` (string)
- **Descripción**: Categoría principal o nivel superior
- **Tipo**: Cadena de texto
- **Restricciones**: 1-100 caracteres, no puede estar vacío
- **Ejemplo**: `"Configuración"`, `"Reportes"`, `"Usuarios"`

```json
{
  "Nivel0": "Configuración"
}
```

#### `Descripcion` (string)
- **Descripción**: Descripción detallada del elemento
- **Tipo**: Cadena de texto
- **Restricciones**: 1-500 caracteres, no puede estar vacío
- **Uso**: Texto principal para búsqueda semántica
- **Ejemplo**: `"Configura las notificaciones y alertas del sistema"`

```json
{
  "Descripcion": "Configura las notificaciones y alertas del sistema"
}
```

#### `url` (string)
- **Descripción**: URL o ruta del elemento
- **Tipo**: Cadena de texto
- **Restricciones**: 1-200 caracteres, no puede estar vacío
- **Formato**: Puede ser URL completa o ruta relativa
- **Ejemplo**: `"localhost/config/alertas"`, `"https://app.com/settings"`

```json
{
  "url": "localhost/config/alertas"
}
```

### Campos Opcionales

#### `Nivel1` (string, opcional)
- **Descripción**: Subcategoría o nivel secundario
- **Tipo**: Cadena de texto
- **Restricciones**: Máximo 100 caracteres
- **Ejemplo**: `"Alertas"`, `"Usuarios"`, `"Reportes"`

```json
{
  "Nivel1": "Alertas"
}
```

#### `keywords` (array, opcional)
- **Descripción**: Palabras clave adicionales para búsqueda
- **Tipo**: Array de strings
- **Uso**: Mejora la precisión de búsqueda semántica
- **Ejemplo**: `["notificaciones", "alertas", "configuración"]`

```json
{
  "keywords": ["notificaciones", "alertas", "configuración"]
}
```

#### `item_type` (string, opcional)
- **Descripción**: Tipo de elemento del menú
- **Tipo**: Enum string
- **Valores permitidos**: 
  - `"configuration"`
  - `"report"`
  - `"user_management"`
  - `"help"`
  - `"other"`

```json
{
  "item_type": "configuration"
}
```

#### `status` (string, opcional)
- **Descripción**: Estado del elemento
- **Tipo**: Enum string
- **Valores permitidos**:
  - `"active"` (por defecto)
  - `"inactive"`
  - `"pending"`
  - `"deleted"`

```json
{
  "status": "active"
}
```

#### `created_at` (string, opcional)
- **Descripción**: Fecha de creación
- **Tipo**: String en formato ISO 8601
- **Ejemplo**: `"2024-01-01T12:00:00Z"`

```json
{
  "created_at": "2024-01-01T12:00:00Z"
}
```

#### `updated_at` (string, opcional)
- **Descripción**: Fecha de última actualización
- **Tipo**: String en formato ISO 8601
- **Ejemplo**: `"2024-01-15T14:30:00Z"`

```json
{
  "updated_at": "2024-01-15T14:30:00Z"
}
```

## 📝 Ejemplo Completo

```json
[
  {
    "ID": 1,
    "Nivel0": "Configuración",
    "Nivel1": "Sistema",
    "Descripcion": "Configurar parámetros generales del sistema",
    "url": "localhost/config/sistema",
    "keywords": ["configuración", "sistema", "parámetros"],
    "item_type": "configuration",
    "status": "active",
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-15T14:30:00Z"
  },
  {
    "ID": 2,
    "Nivel0": "Configuración",
    "Nivel1": "Alertas",
    "Descripcion": "Configura las notificaciones y alertas del sistema",
    "url": "localhost/config/alertas",
    "keywords": ["notificaciones", "alertas", "configuración"],
    "item_type": "configuration",
    "status": "active"
  },
  {
    "ID": 3,
    "Nivel0": "Usuarios",
    "Nivel1": "Gestión",
    "Descripcion": "Administrar usuarios y permisos del sistema",
    "url": "localhost/usuarios/gestion",
    "keywords": ["usuarios", "permisos", "administración"],
    "item_type": "user_management",
    "status": "active"
  },
  {
    "ID": 4,
    "Nivel0": "Reportes",
    "Nivel1": "Ventas",
    "Descripcion": "Generar reportes de ventas y estadísticas",
    "url": "localhost/reportes/ventas",
    "keywords": ["reportes", "ventas", "estadísticas"],
    "item_type": "report",
    "status": "active"
  },
  {
    "ID": 5,
    "Nivel0": "Ayuda",
    "Nivel1": "Documentación",
    "Descripcion": "Acceder a la documentación y guías de usuario",
    "url": "localhost/ayuda/docs",
    "keywords": ["ayuda", "documentación", "guías"],
    "item_type": "help",
    "status": "active"
  }
]
```

## ✅ Validación

El sistema valida automáticamente el formato usando modelos Pydantic. Los errores comunes incluyen:

### Errores de Validación Comunes

1. **ID duplicado**
   ```json
   // ❌ Error: IDs duplicados
   [
     {"ID": 1, "Nivel0": "Test", "Descripcion": "Test 1", "url": "test1"},
     {"ID": 1, "Nivel0": "Test", "Descripcion": "Test 2", "url": "test2"}
   ]
   ```

2. **Campos obligatorios faltantes**
   ```json
   // ❌ Error: Falta campo obligatorio
   {
     "ID": 1,
     "Nivel0": "Test",
     // "Descripcion": "Falta este campo",
     "url": "test"
   }
   ```

3. **Tipos de datos incorrectos**
   ```json
   // ❌ Error: ID debe ser número
   {
     "ID": "1",  // Debe ser número, no string
     "Nivel0": "Test",
     "Descripcion": "Test",
     "url": "test"
   }
   ```

4. **Campos vacíos**
   ```json
   // ❌ Error: Campos no pueden estar vacíos
   {
     "ID": 1,
     "Nivel0": "",  // No puede estar vacío
     "Descripcion": "Test",
     "url": "test"
   }
   ```

## 🔍 Optimización para Búsqueda

### Mejores Prácticas

1. **Descripciones Descriptivas**
   ```json
   // ✅ Bueno: Descripción clara y específica
   {
     "Descripcion": "Configura las notificaciones por email y SMS para alertas del sistema"
   }
   
   // ❌ Malo: Descripción vaga
   {
     "Descripcion": "Configuración"
   }
   ```

2. **Keywords Relevantes**
   ```json
   // ✅ Bueno: Keywords específicas y variadas
   {
     "keywords": ["notificaciones", "email", "SMS", "alertas", "configuración"]
   }
   
   // ❌ Malo: Keywords repetitivas
   {
     "keywords": ["config", "configuración", "configurar"]
   }
   ```

3. **Jerarquía Clara**
   ```json
   // ✅ Bueno: Jerarquía lógica
   {
     "Nivel0": "Configuración",
     "Nivel1": "Notificaciones"
   }
   
   // ❌ Malo: Jerarquía confusa
   {
     "Nivel0": "Sistema",
     "Nivel1": "Configuración de alertas de notificaciones"
   }
   ```

## 🛠 Herramientas de Validación

### Validar Archivo Localmente

```bash
# Validar sintaxis JSON
python -m json.tool data/menu.json

# Validar con el sistema MENU
python indexar.py --dry-run --file data/menu.json
```

### Script de Validación

```python
import json
from app.models.search_models import MenuItem

def validate_menu_json(file_path):
    """Valida un archivo menu.json"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for i, item_data in enumerate(data):
            try:
                MenuItem(**item_data)
                print(f"✅ Elemento {i+1}: Válido")
            except Exception as e:
                print(f"❌ Elemento {i+1}: {e}")
                
    except Exception as e:
        print(f"❌ Error cargando archivo: {e}")

# Uso
validate_menu_json("data/menu.json")
```

## 📊 Estadísticas de Ejemplo

Para un archivo `menu.json` típico:

- **Elementos**: 50-500 elementos
- **Tamaño**: 10KB - 1MB
- **Tiempo de indexación**: 30 segundos - 5 minutos
- **Precisión de búsqueda**: 85-95% con descripciones bien escritas

## 🔄 Migración de Formatos

### Desde CSV

```python
import csv
import json

def csv_to_menu_json(csv_file, json_file):
    """Convierte CSV a formato menu.json"""
    items = []
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 1):
            item = {
                "ID": i,
                "Nivel0": row['categoria'],
                "Nivel1": row.get('subcategoria', ''),
                "Descripcion": row['descripcion'],
                "url": row['url']
            }
            items.append(item)
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(items, f, indent=2, ensure_ascii=False)

# Uso
csv_to_menu_json('data/menu.csv', 'data/menu.json')
```

### Desde Base de Datos

```python
import json
import sqlite3

def db_to_menu_json(db_file, json_file):
    """Convierte base de datos a formato menu.json"""
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, categoria, subcategoria, descripcion, url 
        FROM menu_items 
        WHERE activo = 1
    """)
    
    items = []
    for row in cursor.fetchall():
        item = {
            "ID": row[0],
            "Nivel0": row[1],
            "Nivel1": row[2] or '',
            "Descripcion": row[3],
            "url": row[4]
        }
        items.append(item)
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
    
    conn.close()

# Uso
db_to_menu_json('database.db', 'data/menu.json')
```

---

Para más información sobre la indexación, ver la documentación del [script indexar.py](../README.md#-indexación).