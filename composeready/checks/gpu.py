"""Comprueba que el host tenga runtime NVIDIA si el servicio pide GPU.

Formas de pedir GPU en un compose: la vieja (`runtime: nvidia`), `gpus: all`,
dispositivos CDI (`nvidia.com/gpu=...`) y `deploy.resources.reservations.devices`
con `driver: nvidia`, `capabilities: [gpu]` o `device_ids` CDI. No verifica que el modelo/CUDA concretos vayan a
funcionar — solo que exista al menos un dispositivo `/dev/nvidia*` y el
binario `nvidia-smi`, la comprobación mínima y determinista de "¿hay
GPU aquí siquiera?".
"""

from __future__ import annotations

import glob
import shutil
from typing import Any

from ..finding import Finding


def _is_cdi_gpu(value: Any) -> bool:
    return isinstance(value, str) and value.startswith("nvidia.com/gpu")


def _requests_gpu(service: dict[str, Any]) -> bool:
    if service.get("runtime") == "nvidia":
        return True
    # `gpus: all` (o una lista) es la forma corta actual de Compose.
    if service.get("gpus"):
        return True
    # Dispositivos CDI: `devices: [nvidia.com/gpu=all]`, en forma corta o larga.
    for dev in service.get("devices") or []:
        if _is_cdi_gpu(dev) or (isinstance(dev, dict) and _is_cdi_gpu(dev.get("source"))):
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
        ids = device.get("device_ids")
        if isinstance(ids, list) and any(_is_cdi_gpu(i) for i in ids):
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
