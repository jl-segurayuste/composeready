"""Comprueba que los puertos publicados no estén ya ocupados en el host.

Solo TCP — UDP no se puede comprobar de forma fiable con un simple bind
(muchos servicios UDP no mantienen el socket abierto entre paquetes).
Rangos de puertos (`8080-8090:80-90`) se ignoran deliberadamente: son
poco frecuentes y añaden bastante complejidad de parseo para el valor que
aportan.
"""

from __future__ import annotations

import socket
from typing import Any

from ..compose import resolve_env
from ..finding import Finding


def _short_form_host_port(entry: str) -> int | None:
    body = entry.split("/")[0]  # descarta "/udp", "/tcp"
    if "-" in body:
        return None  # rango, no soportado
    parts = body.split(":")
    if len(parts) == 1:
        return None  # solo puerto de contenedor, no se publica nada
    host_part = parts[-2]
    try:
        return int(host_part)
    except ValueError:
        return None


def _is_port_taken(port: int) -> bool | None:
    """True si está ocupado, False si está libre, None si no se pudo determinar."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
    try:
        sock.bind(("0.0.0.0", port))
    except PermissionError:
        return None
    except OSError:
        return True
    else:
        return False
    finally:
        sock.close()


def check(service_name: str, service: dict[str, Any], env: dict[str, str] | None = None) -> list[Finding]:
    findings: list[Finding] = []
    ports = service.get("ports")
    if not isinstance(ports, list):
        return findings

    for entry in ports:
        host_port: int | None = None
        protocol = "tcp"

        if isinstance(entry, str):
            # "${WEB_PORT:-8080}:80": sin resolver, el "-" del valor por defecto parecía un rango
            # y el puerto no se comprobaba
            entry = resolve_env(entry, env)
            host_port = _short_form_host_port(entry)
            if "/udp" in entry:
                protocol = "udp"
        elif isinstance(entry, int):
            host_port = None  # forma corta "80" sin publicar, nada que comprobar
        elif isinstance(entry, dict):
            published = entry.get("published")
            if isinstance(published, str):
                published = resolve_env(published, env)
            protocol = entry.get("protocol", "tcp")
            if published is not None:
                try:
                    host_port = int(published)
                except (TypeError, ValueError):
                    host_port = None

        if host_port is None or protocol != "tcp":
            continue

        taken = _is_port_taken(host_port)
        if taken:
            findings.append(
                Finding(
                    check="port",
                    service=service_name,
                    message=f"el puerto {host_port}/tcp ya está ocupado en este host",
                    detail="algo (otro contenedor, otro servicio) ya lo tiene enlazado",
                )
            )

    return findings
