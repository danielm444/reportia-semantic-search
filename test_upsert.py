"""Script de prueba para diagnosticar el error de upsert"""
import asyncio
import sys
from datetime import datetime

# Agregar el directorio actual al path
sys.path.insert(0, '.')

from app.api.v1.schemas import UpsertQueryRequest, SavedQueryData
from app.services.search_service import SearchService

async def test_upsert():
    """Prueba el upsert con los datos del ejemplo"""
    
    # Datos del request que estás enviando
    request_data = {
        "query": {
            "company_id": 456,
            "created_at": "2024-01-15T10:30:00Z",
            "description": "Consulta que genera reporte de ventas por mes y región",
            "engine_code": "postgres",
            "id": 123,
            "is_active": True,
            "name": "Reporte de ventas mensuales",
            "owner_user_id": 444,
            "parameters_json": {
                "month": {
                    "default": 1,
                    "type": "integer"
                }
            },
            "query_sql_original": "SELECT * FROM sales WHERE month = ?",
            "query_sql_param": "SELECT * FROM sales WHERE month = :month",
            "updated_at": "2024-01-15T10:30:00Z",
            "version": 1
        }
    }
    
    try:
        # Validar el schema
        print("1. Validando schema...")
        request = UpsertQueryRequest(**request_data)
        print(f"✓ Schema válido: {request.query.id}")
        
        # Convertir a dict
        print("\n2. Convirtiendo a dict...")
        query_data = request.query.model_dump()
        print(f"✓ Dict creado con {len(query_data)} campos")
        
        # Intentar upsert
        print("\n3. Intentando upsert...")
        search_service = SearchService()
        result = await search_service.upsert_query(query_data)
        print(f"✓ Upsert exitoso: {result}")
        
    except Exception as e:
        print(f"\n✗ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_upsert())
