"""Carga de un fichero docker-compose y utilidades comunes a los checks."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml

_VAR_RE = re.compile(
    r"\$\{(?P<name>[A-Za-z_][A-Za-z0-9_]*)(?:(?P<colon>:)?-(?P<default>[^}]*))?\}|\$(?P<bare>[A-Za-z_][A-Za-z0-9_]*)"
)


def resolve_env(text: str, env: dict[str, str] | None = None) -> str:
    """Sustituye ${VAR}, ${VAR:-default} y $VAR usando el entorno real.

    Si una variable no está definida y no tiene default, se deja el texto
    literal tal cual (mejor un falso negativo aislado que reventar aquí).
    """
    env = os.environ if env is None else env

    def _sub(m: re.Match[str]) -> str:
        name = m.group("name") or m.group("bare")
        default = m.group("default")
        # ${VAR:-x} usa x también si VAR está vacía; ${VAR-x}, solo si no existe
        if name in env and not (m.group("colon") and default is not None and env[name] == ""):
            return env[name]
        return default if default is not None else m.group(0)

    return _VAR_RE.sub(_sub, text)


def load_dotenv(path: Path) -> dict[str, str]:
    """Variables de un `.env` (CLAVE=valor; admite comillas y `export`)."""
    values: dict[str, str] = {}
    try:
        lines = path.read_text(errors="replace").splitlines()
    except OSError:
        return values
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.removeprefix("export ").partition("=")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        else:
            value = value.split(" #", 1)[0].strip()
        values[key.strip()] = value
    return values


def project_env(compose_dir: Path) -> dict[str, str]:
    """Variables con las que docker compose interpola el fichero: el `.env` de la carpeta del
    proyecto y, por encima, el entorno. Antes solo se miraba el entorno y, con el puerto o la ruta
    en el `.env`, se comprobaba el valor por defecto en vez del real."""
    return {**load_dotenv(compose_dir / ".env"), **os.environ}


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
