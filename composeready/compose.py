"""Carga de un fichero docker-compose y utilidades comunes a los checks."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml

_VAR_RE = re.compile(r"\$\{(?P<name>[A-Za-z_][A-Za-z0-9_]*)(?::?-(?P<default>[^}]*))?\}|\$(?P<bare>[A-Za-z_][A-Za-z0-9_]*)")


def resolve_env(text: str, env: dict[str, str] | None = None) -> str:
    """Sustituye ${VAR}, ${VAR:-default} y $VAR usando el entorno real.

    Si una variable no está definida y no tiene default, se deja el texto
    literal tal cual (mejor un falso negativo aislado que reventar aquí).
    """
    env = os.environ if env is None else env

    def _sub(m: re.Match[str]) -> str:
        name = m.group("name") or m.group("bare")
        if name in env:
            return env[name]
        default = m.group("default")
        return default if default is not None else m.group(0)

    return _VAR_RE.sub(_sub, text)


def load_compose(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(errors="replace"))
    if not isinstance(data, dict):
        return {}
    return data


def iter_services(data: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    services = data.get("services")
    if not isinstance(services, dict):
        return []
    return [(name, svc) for name, svc in services.items() if isinstance(svc, dict)]


def find_compose_file(path: Path) -> Path | None:
    if path.is_file():
        return path
    for name in ("docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"):
        candidate = path / name
        if candidate.is_file():
            return candidate
    return None
