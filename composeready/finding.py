"""Modelo de datos compartido por todos los checks."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Finding:
    """Algo que este compose asume del host y que el host, ahora mismo, no cumple."""

    check: str
    service: str
    message: str
    detail: str

    def format(self) -> str:
        return f"[{self.check}] servicio '{self.service}': {self.message}\n    {self.detail}"
