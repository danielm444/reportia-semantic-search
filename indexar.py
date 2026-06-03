#!/usr/bin/env python3
"""
Script independiente de indexación para el sistema MENU.

Indexa los elementos de `data/menu.json` en Qdrant aplicando la estrategia
"scorched earth": elimina la colección existente y la reconstruye desde cero
para garantizar consistencia entre el archivo fuente y la base de datos vectorial.
"""

import os
import sys
import json
import time
import asyncio
import argparse
from typing import List, Dict, Any, Tuple

# Añadir el directorio raíz al path para imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config.settings import settings
from app.core.logging import setup_logging, get_logger
from app.core.exceptions import IndexingError, ConfigurationError
from app.services.embedding_service import get_embedding_service
from app.services.qdrant_service import get_qdrant_service
from app.services.search_service import get_search_service
from app.models.search_models import MenuItem

# Dimensión de los vectores de text-embedding-3-small (OpenAI)
VECTOR_SIZE = 1536


def setup_indexing_logger():
    """Configura logging específico para indexación."""
    setup_logging()
    logger = get_logger("indexar")
    logger.info("Script de indexación iniciado")
    return logger


def validate_environment():
    """
    Valida que el entorno esté configurado correctamente y que Qdrant
    esté accesible antes de comenzar.

    Raises:
        ConfigurationError: Si la configuración es inválida
        IndexingError: Si Qdrant no está disponible
    """
    logger = get_logger("indexar")

    # Validar configuración
    try:
        settings.validate_configuration()
        logger.info("Configuración validada correctamente")
    except Exception as e:
        logger.error(f"Error en configuración: {e}")
        raise ConfigurationError(f"Configuración inválida: {e}")

    # Verificar conexión con Qdrant
    qdrant_service = get_qdrant_service()
    health = qdrant_service.health_check()
    if health.get("status") != "healthy":
        raise IndexingError(
            f"Qdrant no está disponible en {qdrant_service.url}: "
            f"{health.get('error', 'estado desconocido')}"
        )

    logger.info(
        f"Conexión con Qdrant verificada: {qdrant_service.url} "
        f"(colección: {qdrant_service.collection_name})"
    )


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
                # Detectar formato y normalizar si es necesario
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

    except IndexingError:
        raise
    except Exception as e:
        logger.error(f"Error durante validación: {e}")
        raise IndexingError(f"Error validando datos: {e}")


def build_index_entries(
    menu_items: List[MenuItem],
    debug_text: bool = False
) -> List[Tuple[int, str, Dict[str, Any]]]:
    """
    Construye las entradas a indexar a partir de los elementos del menú.

    A diferencia de ChromaDB, Qdrant acepta payloads estructurados (listas y
    objetos anidados), por lo que no es necesario aplanar los metadatos.

    Args:
        menu_items: Lista de elementos del menú validados
        debug_text: Si incluir el texto indexado generado en el payload

    Returns:
        List[Tuple[int, str, Dict]]: Tuplas (point_id, texto_a_embeber, payload)
    """
    logger = get_logger("indexar")

    try:
        entries: List[Tuple[int, str, Dict[str, Any]]] = []
        format_stats = {"actual": 0, "extendido": 0, "con_texto_indexado": 0}
        seen_ids = set()

        for item in menu_items:
            # Texto canónico normalizado para búsqueda semántica
            search_text = item.to_search_text()

            point_id = item.get_effective_id()
            if point_id in seen_ids:
                logger.warning(f"ID duplicado detectado, se sobrescribirá: {point_id}")
            seen_ids.add(point_id)

            # Payload estructurado con los campos relevantes del menú.
            # Se omiten los None para mantener el payload limpio.
            payload = {
                "id": point_id,
                "titulo": item.titulo or item.Nivel0,
                "Nivel0": item.Nivel0,
                "Nivel1": item.Nivel1,
                "nivel": item.nivel,
                "Descripcion": item.get_effective_description(),
                "url": item.url,
                "sinonimos": item.sinonimos,
                "acciones": item.acciones,
                "keywords": item.keywords,
                "tipo": item.tipo,
                "estado": item.get_effective_status(),
                "idioma": item.idioma,
            }
            payload = {k: v for k, v in payload.items() if v is not None}

            if debug_text:
                payload["texto_indexado_generado"] = search_text

            # Estadísticas de formato
            if item.is_extended_format():
                format_stats["extendido"] += 1
            else:
                format_stats["actual"] += 1
            if item.texto_indexado:
                format_stats["con_texto_indexado"] += 1

            entries.append((point_id, search_text, payload))

        logger.info(f"Entradas de indexación creadas: {len(entries)}")
        logger.info(f"Formato actual: {format_stats['actual']}, "
                    f"Formato extendido: {format_stats['extendido']}, "
                    f"Con texto pre-calculado: {format_stats['con_texto_indexado']}")

        return entries

    except Exception as e:
        logger.error(f"Error creando entradas de indexación: {e}")
        raise IndexingError(f"Error creando entradas de indexación: {e}")


async def index_entries(entries: List[Tuple[int, str, Dict[str, Any]]]) -> None:
    """
    Indexa las entradas en una colección de Qdrant recién creada (scorched earth).

    Args:
        entries: Tuplas (point_id, texto_a_embeber, payload)

    Raises:
        IndexingError: Si falla la indexación
    """
    logger = get_logger("indexar")

    try:
        logger.info(f"Iniciando indexación de {len(entries)} entradas")

        # 1. Scorched earth: recrear la colección desde cero
        logger.info("Recreando colección en Qdrant (scorched earth)")
        get_qdrant_service().recreate_collection(vector_size=VECTOR_SIZE)

        # 2. Indexar vía el núcleo genérico (embeddings + upsert en lote)
        documents = [
            {"id": point_id, "texto": text, "payload": payload}
            for point_id, text, payload in entries
        ]
        result = await get_search_service().upsert_documents(documents)

        if result["count"] != len(entries):
            raise IndexingError(
                f"Discrepancia en indexación: {result['count']} indexados "
                f"vs {len(entries)} esperados"
            )

        logger.info("Indexación completada exitosamente")

    except IndexingError:
        raise
    except Exception as e:
        logger.error(f"Error durante indexación: {e}")
        raise IndexingError(f"Error indexando entradas: {e}")


async def verify_indexing(expected_count: int) -> None:
    """
    Verifica que la indexación fue exitosa consultando Qdrant directamente.

    Args:
        expected_count: Número esperado de puntos indexados

    Raises:
        IndexingError: Si la verificación de conteo falla
    """
    logger = get_logger("indexar")

    try:
        logger.info("Verificando indexación...")

        embedding_service = get_embedding_service()
        qdrant_service = get_qdrant_service()

        # 1. Validación estricta de conteo
        collection_info = qdrant_service.get_collection_info()
        indexed_count = collection_info.get("points_count", 0)

        logger.info(f"Elementos originales: {expected_count}")
        logger.info(f"Puntos indexados: {indexed_count}")

        if indexed_count != expected_count:
            raise IndexingError(
                f"Discrepancia en conteo: {indexed_count} indexados "
                f"vs {expected_count} originales"
            )

        # 2. Prueba de búsqueda semántica con medición de tiempo
        try:
            from app.core.text_normalizer import normalize_query

            start_time = time.time()
            query_vector = await embedding_service.embed_query(
                normalize_query("configuración")
            )
            results = qdrant_service.search_similar(query_vector=query_vector, limit=3)
            search_time = time.time() - start_time

            logger.info(
                f"Prueba de búsqueda exitosa: {len(results)} resultados "
                f"en {search_time:.3f}s"
            )

            if results:
                top = results[0]
                logger.info(
                    f"Resultado top: '{top['payload'].get('titulo')}' "
                    f"(score={top['score']:.4f})"
                )

            if search_time >= 2.0:
                logger.warning(f"Tiempo de búsqueda excede límite: {search_time:.3f}s >= 2.0s")
            else:
                logger.info(f"Tiempo de búsqueda dentro del límite: {search_time:.3f}s < 2.0s")

        except Exception as e:
            logger.warning(f"Prueba de búsqueda falló (puede ser por API key): {e}")

        logger.info("Verificación completada exitosamente")

    except IndexingError:
        raise
    except Exception as e:
        logger.error(f"Error durante verificación: {e}")
        raise IndexingError(f"Error verificando indexación: {e}")


async def run_indexing(args) -> None:
    """Orquesta el flujo completo de indexación."""
    logger = get_logger("indexar")
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

    # 4. Construir entradas de indexación
    logger.info("Paso 4: Construyendo entradas de indexación...")
    entries = build_index_entries(menu_items, debug_text=args.debug_text)

    if args.dry_run:
        logger.info("=== MODO DRY-RUN: No se realizarán cambios ===")
        logger.info(f"Se procesarían {len(entries)} elementos")
        return

    # 5. Indexar en Qdrant (incluye scorched earth)
    logger.info("Paso 5: Indexando en Qdrant...")
    await index_entries(entries)

    # 6. Verificar indexación
    logger.info("Paso 6: Verificando indexación...")
    await verify_indexing(len(entries))

    # Resumen final con métricas de rendimiento
    processing_time = time.time() - start_time
    docs_per_second = len(menu_items) / processing_time if processing_time > 0 else 0
    avg_time_per_doc = processing_time / len(menu_items) if len(menu_items) > 0 else 0

    logger.info("=== INDEXACIÓN COMPLETADA ===")
    logger.info(f"Documentos procesados: {len(menu_items)}")
    logger.info(f"Tiempo de procesamiento: {processing_time:.2f} segundos")
    logger.info(f"Velocidad: {docs_per_second:.2f} docs/segundo")
    logger.info(f"Tiempo promedio por documento: {avg_time_per_doc:.3f} segundos")
    logger.info(f"Colección Qdrant: {get_qdrant_service().collection_name}")

    if processing_time > 300:  # 5 minutos
        logger.warning(f"Tiempo de indexación alto: {processing_time:.2f} segundos")

    print(f"\n✅ Indexación completada exitosamente!")
    print(f"📊 Documentos procesados: {len(menu_items)}")
    print(f"⏱️  Tiempo: {processing_time:.2f} segundos")
    print(f"🚀 Velocidad: {docs_per_second:.1f} docs/segundo")


def main():
    """Función principal del script de indexación."""
    parser = argparse.ArgumentParser(description="Script de indexación MENU (Qdrant)")
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
        help="Incluir el texto indexado generado en el payload para debugging"
    )

    args = parser.parse_args()

    # Configurar logging
    if args.verbose:
        os.environ["LOG_LEVEL"] = "DEBUG"

    setup_indexing_logger()

    try:
        asyncio.run(run_indexing(args))
    except KeyboardInterrupt:
        get_logger("indexar").warning("Indexación interrumpida por el usuario")
        print("\n⚠️  Indexación interrumpida")
        sys.exit(1)
    except Exception as e:
        get_logger("indexar").error(f"Error durante indexación: {e}")
        print(f"\n❌ Error durante indexación: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
