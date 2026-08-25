"""Comprueba que el host tenga runtime NVIDIA si el servicio pide GPU.

Dos formas de pedir GPU en un compose: la vieja (`runtime: nvidia`) y la
actual (`deploy.resources.reservations.devices` con `driver: nvidia` o
`capabilities: [gpu]`). No verifica que el modelo/CUDA concretos vayan a
funcionar — solo que exista al menos un dispositivo `/dev/nvidia*` y el
binario `nvidia-smi`, la comprobación mínima y determinista de "¿hay
GPU aquí siquiera?".
"""

from __future__ import annotations

import glob
import shutil
from typing import Any

from ..finding import Finding


def _requests_gpu(service: dict[str, Any]) -> bool:
    if service.get("runtime") == "nvidia":
        return True

    deploy = service.get("deploy")
    if not isinstance(deploy, dict):
        return False
    resources = deploy.get("resources")
    if not isinstance(resources, dict):
        return False
    reservations = resources.get("reservations")
    if not isinstance(reservations, dict):
        return False
    devices = reservations.get("devices")
    if not isinstance(devices, list):
        return False

    for device in devices:
        if not isinstance(device, dict):
            continue
        if device.get("driver") == "nvidia":
            return True
        capabilities = device.get("capabilities")
        if isinstance(capabilities, list) and "gpu" in capabilities:
            return True

    return False


def check(service_name: str, service: dict[str, Any]) -> list[Finding]:
    if not _requests_gpu(service):
        return []

    problems = []
    if not glob.glob("/dev/nvidia*"):
        problems.append("no se encontró ningún /dev/nvidia* en este host")
    if shutil.which("nvidia-smi") is None:
        problems.append("nvidia-smi no está en el PATH")

    if not problems:
        return []

    return [
        Finding(
            check="gpu",
            service=service_name,
            message="pide GPU NVIDIA pero este host no parece tenerla lista",
            detail="; ".join(problems),
        )
    ]
