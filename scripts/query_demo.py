#!/usr/bin/env python3
"""Demo de búsqueda semántica REAL (OpenAI + Qdrant en vivo) sobre menu.json."""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.search_service import get_search_service


QUERIES = [
    ("donde gestiono los usuarios y sus permisos", None),
    ("quiero ver reportes del tiempo promedio de atención", None),
    ("configurar los días feriados y no laborables", None),
    ("sacar un turno nuevo en la agenda", None),
    ("administrar pantallas y totems de autogestión", None),
    ("auditar los inicios de sesión", {"tipo": "security"}),
]


async def main():
    svc = get_search_service()
    for q, filtros in QUERIES:
        res = await svc.search(q, top_k=3, filters=filtros)
        flt = f"  (filtro={filtros})" if filtros else ""
        print(f"\n🔎 {q!r}{flt}")
        for i, r in enumerate(res, 1):
            d = r["data"]
            print(f"   {i}. score={r['score']:.4f}  {d.get('titulo')}  [{d.get('tipo')}]  -> {d.get('url')}")


if __name__ == "__main__":
    asyncio.run(main())
