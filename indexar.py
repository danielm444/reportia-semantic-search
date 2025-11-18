#!/usr/bin/env python3
"""
Script independiente de indexación para el sistema MENU.
Implementa la estrategia "scorched earth" para garantizar consistencia.
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Añadir el directorio raíz al path para imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langchain_core.documents import Document
from langchain_community.document_loaders import JSONLoader
from app.config.settings import settings
from app.core.logging import setup_logging, get_logger
from app.core.exceptions import IndexingError, ConfigurationError
from app.services.embedding_service import EmbeddingService
from app.services.search_service import SearchService
from app.models.search_models import MenuItem


def setup_indexing_logger():
    """Configura logging específico para indexación."""
    setup_logging()
    logger = get_logger("indexar")
    logger.info("Script de indexación iniciado")
    return logger


def validate_environment():
    """
    Valida que el entorno esté configurado correctamente.
    
    Raises:
        ConfigurationError: Si la configuración es inválida
    """
    logger = get_logger("indexar")
    
    # Validar configuración
    try:
        settings.validate_configuration()
        logger.info("Configuración validada correctamente")
    except Exception as e:
        logger.error(f"Error en configuración: {e}")
        raise ConfigurationError(f"Configuración inválida: {e}")
    
    # Verificar que el directorio de ChromaDB existe
    if not os.path.exists(settings.chroma_db_path):
        logger.info(f"Creando directorio ChromaDB: {settings.chroma_db_path}")
        os.makedirs(settings.chroma_db_path, exist_ok=True)


def load_menu_data(file_path: str) -> List[Dict[str, Any]]:
    """
    Carga datos del archivo menu.json.
    
    Args:
        file_path: Ruta al archivo JSON
        
    Returns:
        List[Dict[str, Any]]: Lista de elementos del menú
        
    Raises:
        IndexingError: Si falla la carga del archivo
    """
    logger = get_logger("indexar")
    
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
        
        logger.info(f"Cargando datos desde: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            raise ValueError("El archivo JSON debe contener una lista de elementos")
        
        logger.info(f"Datos cargados exitosamente: {len(data)} elementos")
        return data
        
    except FileNotFoundError as e:
        logger.error(f"Archivo no encontrado: {e}")
        raise IndexingError(f"Archivo no encontrado: {e}", file_path=file_path)
    except json.JSONDecodeError as e:
        logger.error(f"Error parseando JSON: {e}")
        raise IndexingError(f"JSON inválido: {e}", file_path=file_path)
    except Exception as e:
        logger.error(f"Error cargando datos: {e}")
        raise IndexingError(f"Error cargando datos: {e}", file_path=file_path)


def validate_menu_items(data: List[Dict[str, Any]]) -> List[MenuItem]:
    """
    Valida y convierte los datos a modelos MenuItem.
    Soporta formato actual y extendido del JSON.
    
    Args:
        data: Lista de diccionarios con datos del menú
        
    Returns:
        List[MenuItem]: Lista de elementos validados
        
    Raises:
        IndexingError: Si la validación falla
    """
    logger = get_logger("indexar")
    
    try:
        validated_items = []
        errors = []
        format_compatibility = {"actual": 0, "extendido": 0, "mixto": 0}
        
        for i, item_data in enumerate(data):
            try:
                # NUEVO: Detectar formato y normalizar si es necesario
                normalized_data = normalize_item_format(item_data)
                
                # Validar usando el modelo Pydantic
                menu_item = MenuItem(**normalized_data)
                validated_items.append(menu_item)
                
                # Estadísticas de formato
                if has_extended_fields(item_data):
                    if has_current_fields(item_data):
                        format_compatibility["mixto"] += 1
                    else:
                        format_compatibility["extendido"] += 1
                else:
                    format_compatibility["actual"] += 1
                    
            except Exception as e:
                error_msg = f"Elemento {i}: {e}"
                errors.append(error_msg)
                logger.warning(error_msg)
        
        if errors:
            logger.warning(f"Se encontraron {len(errors)} errores de validación")
            if len(errors) > len(data) * 0.5:  # Más del 50% con errores
                raise IndexingError(
                    f"Demasiados errores de validación: {len(errors)}/{len(data)}"
                )
        
        logger.info(f"Validación completada: {len(validated_items)} elementos válidos")
        logger.info(f"Compatibilidad: Actual={format_compatibility['actual']}, "
                   f"Extendido={format_compatibility['extendido']}, "
                   f"Mixto={format_compatibility['mixto']}")
        
        return validated_items
        
    except Exception as e:
        logger.error(f"Error durante validación: {e}")
        raise IndexingError(f"Error validando datos: {e}")


def has_extended_fields(item_data: Dict[str, Any]) -> bool:
    """Verifica si el elemento tiene campos del formato extendido."""
    extended_fields = ["id", "titulo", "nivel", "descripcion", "sinonimos", "acciones", "texto_indexado"]
    return any(field in item_data for field in extended_fields)


def has_current_fields(item_data: Dict[str, Any]) -> bool:
    """Verifica si el elemento tiene campos del formato actual."""
    current_fields = ["ID", "Nivel0", "Nivel1", "Descripcion"]
    return any(field in item_data for field in current_fields)


def normalize_item_format(item_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normaliza un elemento para que sea compatible con ambos formatos.
    Convierte formato extendido a formato actual cuando sea necesario.
    """
    normalized = item_data.copy()
    
    # Si tiene formato extendido, mapear a campos actuales para compatibilidad
    if "id" in item_data and "ID" not in item_data:
        normalized["ID"] = item_data["id"]
    
    if "nivel" in item_data and isinstance(item_data["nivel"], list):
        if "Nivel0" not in item_data and len(item_data["nivel"]) > 0:
            normalized["Nivel0"] = item_data["nivel"][0]
        if "Nivel1" not in item_data and len(item_data["nivel"]) > 1:
            normalized["Nivel1"] = item_data["nivel"][1]
    
    if "descripcion" in item_data and "Descripcion" not in item_data:
        normalized["Descripcion"] = item_data["descripcion"]
    
    # Mapear estado
    if "estado" in item_data and "status" not in item_data:
        normalized["status"] = item_data["estado"]
    
    # Mapear tipo
    if "tipo" in item_data and "item_type" not in item_data:
        normalized["item_type"] = item_data["tipo"]
    
    return normalized


def create_langchain_documents(menu_items: List[MenuItem], debug_text: bool = False) -> List[Document]:
    """
    Convierte elementos del menú a documentos de LangChain.
    Soporta formato actual y extendido del JSON.
    
    Args:
        menu_items: Lista de elementos del menú validados
        debug_text: Si incluir texto indexado en metadata para debugging
        
    Returns:
        List[Document]: Lista de documentos para LangChain
    """
    logger = get_logger("indexar")
    
    try:
        documents = []
        format_stats = {"actual": 0, "extendido": 0, "con_texto_indexado": 0}
        
        for item in menu_items:
            # Crear texto para búsqueda semántica usando método optimizado
            page_content = item.to_search_text()
            
            # Usar el diccionario completo como metadata, pero filtrar tipos complejos
            metadata = item.model_dump(exclude_none=True)
            
            # NUEVO: Filtrar metadatos complejos que ChromaDB no acepta
            filtered_metadata = {}
            for key, value in metadata.items():
                if isinstance(value, (str, int, float, bool)) or value is None:
                    filtered_metadata[key] = value
                elif isinstance(value, list):
                    # Convertir listas a strings separadas por comas
                    if all(isinstance(item, str) for item in value):
                        filtered_metadata[f"{key}_str"] = ", ".join(value)
                    else:
                        filtered_metadata[f"{key}_str"] = str(value)
                elif isinstance(value, dict):
                    # Convertir diccionarios a string JSON
                    import json
                    filtered_metadata[f"{key}_json"] = json.dumps(value)
                else:
                    # Otros tipos complejos convertir a string
                    filtered_metadata[f"{key}_str"] = str(value)
            
            # Estadísticas de formato
            if item.is_extended_format():
                format_stats["extendido"] += 1
            else:
                format_stats["actual"] += 1
            
            if item.texto_indexado:
                format_stats["con_texto_indexado"] += 1
            
            # NUEVO: Incluir texto indexado para debugging si se solicita
            if debug_text:
                filtered_metadata["texto_indexado_generado"] = page_content
            
            # Crear documento de LangChain
            doc = Document(
                page_content=page_content,
                metadata=filtered_metadata
            )
            
            documents.append(doc)
        
        logger.info(f"Documentos LangChain creados: {len(documents)}")
        logger.info(f"Formato actual: {format_stats['actual']}, "
                   f"Formato extendido: {format_stats['extendido']}, "
                   f"Con texto pre-calculado: {format_stats['con_texto_indexado']}")
        
        return documents
        
    except Exception as e:
        logger.error(f"Error creando documentos LangChain: {e}")
        raise IndexingError(f"Error creando documentos: {e}")


def delete_existing_collection():
    """
    Elimina la colección existente (estrategia scorched earth).
    
    Raises:
        IndexingError: Si falla la eliminación
    """
    logger = get_logger("indexar")
    
    try:
        import shutil
        import os
        import time
        
        logger.warning("Iniciando eliminación de colección existente (scorched earth)")
        
        # Método directo: eliminar todo el directorio ChromaDB
        if os.path.exists(settings.chroma_db_path):
            try:
                # Intentar eliminar el directorio completo
                shutil.rmtree(settings.chroma_db_path)
                logger.info("Directorio ChromaDB eliminado completamente")
                
                # Esperar un momento para asegurar que el sistema libere los archivos
                time.sleep(0.5)
                
                # Recrear el directorio vacío
                os.makedirs(settings.chroma_db_path, exist_ok=True)
                logger.info("Directorio ChromaDB recreado")
                
            except PermissionError as e:
                logger.warning(f"No se pudo eliminar directorio (archivos en uso): {e}")
                # Si no se puede eliminar, intentar renombrar el directorio
                backup_path = f"{settings.chroma_db_path}_backup_{int(time.time())}"
                try:
                    os.rename(settings.chroma_db_path, backup_path)
                    os.makedirs(settings.chroma_db_path, exist_ok=True)
                    logger.info(f"Directorio renombrado a {backup_path} y recreado")
                except Exception as rename_error:
                    logger.error(f"No se pudo renombrar directorio: {rename_error}")
                    raise IndexingError(f"No se puede limpiar la base de datos: {rename_error}")
        else:
            logger.info("Directorio ChromaDB no existe, creando nuevo")
            os.makedirs(settings.chroma_db_path, exist_ok=True)
        
    except Exception as e:
        logger.error(f"Error durante eliminación de colección: {e}")
        raise IndexingError(f"Error eliminando colección: {e}")


def index_documents(documents: List[Document]) -> SearchService:
    """
    Indexa los documentos en la nueva colección.
    
    Args:
        documents: Lista de documentos a indexar
        
    Returns:
        SearchService: Servicio de búsqueda con los nuevos datos
        
    Raises:
        IndexingError: Si falla la indexación
    """
    logger = get_logger("indexar")
    
    try:
        logger.info(f"Iniciando indexación de {len(documents)} documentos")
        
        # Crear servicios
        embedding_service = EmbeddingService()
        
        # Crear nueva colección desde documentos
        search_service = SearchService().create_from_documents(
            documents=documents,
            embedding_service=embedding_service
        )
        
        logger.info("Indexación completada exitosamente")
        return search_service
        
    except Exception as e:
        logger.error(f"Error durante indexación: {e}")
        raise IndexingError(f"Error indexando documentos: {e}")


def verify_indexing(search_service: SearchService, original_count: int):
    """
    Verifica que la indexación fue exitosa con validaciones de rendimiento.
    
    Args:
        search_service: Servicio de búsqueda
        original_count: Número original de documentos
        
    Raises:
        IndexingError: Si la verificación falla
    """
    logger = get_logger("indexar")
    
    try:
        logger.info("Verificando indexación...")
        
        # NUEVO: Obtener información detallada de la colección
        collection_info = search_service.get_collection_info()
        indexed_count = collection_info.get('document_count', 0)
        
        logger.info(f"Documentos originales: {original_count}")
        logger.info(f"Documentos indexados: {indexed_count}")
        
        # NUEVO: Validación estricta de conteo
        if indexed_count != original_count:
            raise IndexingError(
                f"Discrepancia en conteo: {indexed_count} indexados vs {original_count} originales"
            )
        
        # NUEVO: Probar búsqueda con medición de tiempo
        try:
            import time
            start_time = time.time()
            test_results = search_service.search_sync("configuración", top_k=3)
            search_time = time.time() - start_time
            
            logger.info(f"Prueba de búsqueda exitosa: {len(test_results)} resultados en {search_time:.3f}s")
            
            # NUEVO: Validar tiempo de respuesta
            if search_time >= 2.0:
                logger.warning(f"Tiempo de búsqueda excede límite: {search_time:.3f}s >= 2.0s")
            else:
                logger.info(f"Tiempo de búsqueda dentro del límite: {search_time:.3f}s < 2.0s")
            
            # NUEVO: Probar búsqueda con tildes para validar normalización
            start_time = time.time()
            test_results_tildes = search_service.search_sync("configuración", top_k=3)
            search_time_tildes = time.time() - start_time
            
            logger.info(f"Prueba con tildes: {len(test_results_tildes)} resultados en {search_time_tildes:.3f}s")
            
        except Exception as e:
            logger.warning(f"Prueba de búsqueda falló (puede ser por API key): {e}")
        
        # NUEVO: Verificar health check del servicio
        try:
            health_status = search_service.health_check()
            if health_status.get("status") == "healthy":
                logger.info("Health check del servicio: OK")
            else:
                logger.warning(f"Health check del servicio: {health_status}")
        except Exception as e:
            logger.warning(f"Health check falló: {e}")
        
        logger.info("Verificación completada exitosamente")
        
    except Exception as e:
        logger.error(f"Error durante verificación: {e}")
        raise IndexingError(f"Error verificando indexación: {e}")


def main():
    """Función principal del script de indexación."""
    parser = argparse.ArgumentParser(description="Script de indexación MENU")
    parser.add_argument(
        "--file", 
        default="data/menu.json",
        help="Ruta al archivo JSON de datos (default: data/menu.json)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Ejecutar sin hacer cambios reales"
    )
    parser.add_argument(
        "--verbose",
        action="store_true", 
        help="Logging detallado"
    )
    parser.add_argument(
        "--debug-text",
        action="store_true",
        help="Incluir texto indexado en metadata para debugging"
    )
    
    args = parser.parse_args()
    
    # Configurar logging
    if args.verbose:
        os.environ["LOG_LEVEL"] = "DEBUG"
    
    logger = setup_indexing_logger()
    
    try:
        start_time = time.time()
        
        logger.info("=== INICIO DE INDEXACIÓN ===")
        logger.info(f"Archivo de datos: {args.file}")
        logger.info(f"Modo dry-run: {args.dry_run}")
        
        # 1. Validar entorno
        logger.info("Paso 1: Validando entorno...")
        validate_environment()
        
        # 2. Cargar datos
        logger.info("Paso 2: Cargando datos...")
        raw_data = load_menu_data(args.file)
        
        # 3. Validar datos
        logger.info("Paso 3: Validando datos...")
        menu_items = validate_menu_items(raw_data)
        
        # 4. Crear documentos LangChain
        logger.info("Paso 4: Creando documentos LangChain...")
        documents = create_langchain_documents(menu_items, debug_text=args.debug_text)
        
        if args.dry_run:
            logger.info("=== MODO DRY-RUN: No se realizarán cambios ===")
            logger.info(f"Se procesarían {len(documents)} documentos")
            return
        
        # 5. Eliminar colección existente (scorched earth)
        logger.info("Paso 5: Eliminando colección existente...")
        delete_existing_collection()
        
        # 6. Indexar documentos
        logger.info("Paso 6: Indexando documentos...")
        search_service = index_documents(documents)
        
        # 7. Verificar indexación
        logger.info("Paso 7: Verificando indexación...")
        verify_indexing(search_service, len(menu_items))
        
        # Resumen final con métricas de rendimiento
        end_time = time.time()
        processing_time = end_time - start_time
        
        # NUEVO: Calcular métricas de rendimiento
        docs_per_second = len(menu_items) / processing_time if processing_time > 0 else 0
        avg_time_per_doc = processing_time / len(menu_items) if len(menu_items) > 0 else 0
        
        logger.info("=== INDEXACIÓN COMPLETADA ===")
        logger.info(f"Documentos procesados: {len(menu_items)}")
        logger.info(f"Tiempo de procesamiento: {processing_time:.2f} segundos")
        logger.info(f"Velocidad: {docs_per_second:.2f} docs/segundo")
        logger.info(f"Tiempo promedio por documento: {avg_time_per_doc:.3f} segundos")
        logger.info(f"Base de datos: {settings.chroma_db_path}")
        
        # NUEVO: Validar que el tiempo de indexación sea razonable
        if processing_time > 300:  # 5 minutos
            logger.warning(f"Tiempo de indexación alto: {processing_time:.2f} segundos")
        
        print(f"\n✅ Indexación completada exitosamente!")
        print(f"📊 Documentos procesados: {len(menu_items)}")
        print(f"⏱️  Tiempo: {processing_time:.2f} segundos")
        print(f"🚀 Velocidad: {docs_per_second:.1f} docs/segundo")
        
    except KeyboardInterrupt:
        logger.warning("Indexación interrumpida por el usuario")
        print("\n⚠️  Indexación interrumpida")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error durante indexación: {e}")
        print(f"\n❌ Error durante indexación: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()