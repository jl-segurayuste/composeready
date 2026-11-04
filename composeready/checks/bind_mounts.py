"""Comprueba que las rutas de origen de los bind-mounts existan en el host.

Ignora los volúmenes con nombre (`mydata:/app/data`) — solo mira rutas de
host explícitas, ya sean relativas (`./data:...`), absolutas (`/srv/...`)
o con `~`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..compose import resolve_env
from ..finding import Finding


def _looks_like_host_path(source: str) -> bool:
    return source.startswith((".", "/", "~"))


def _short_form_source(entry: str) -> str | None:
    # "./host:/container[:ro]" o "/abs/host:/container[:ro]" — el primer
    # ':' separa host de container, salvo que sea una letra de unidad de
    # Windows (poco relevante aquí, pero evita cortar mal "C:\...").
    parts = entry.split(":")
    if len(parts) < 2:
        return None
    source = parts[0]
    return source if _looks_like_host_path(source) else None


def check(
    service_name: str, service: dict[str, Any], compose_dir: Path, env: dict[str, str] | None = None
) -> list[Finding]:
    findings: list[Finding] = []
    volumes = service.get("volumes")
    if not isinstance(volumes, list):
        return findings

    for entry in volumes:
        source: str | None = None

        if isinstance(entry, str):
            source = _short_form_source(resolve_env(entry, env))
        elif isinstance(entry, dict) and entry.get("type") == "bind":
            raw = entry.get("source")
            if isinstance(raw, str):
                resolved = resolve_env(raw, env)
                if _looks_like_host_path(resolved) or Path(resolved).is_absolute():
                    source = resolved

        if source is None:
            continue

        resolved_path = Path(source).expanduser()
        if not resolved_path.is_absolute():
            resolved_path = compose_dir / resolved_path

        if not resolved_path.exists():
            findings.append(
                Finding(
                    check="bind_mount",
                    service=service_name,
                    message=f"la ruta de origen '{source}' no existe en este host",
                    detail=f"se resolvió a: {resolved_path}",
                )
            )

    return findings
