# Contribuir

## Añadir un check nuevo

Cada check vive en `composeready/checks/` como un módulo independiente con
una función `check(service_name, service, ...) -> list[Finding]`. Añádelo
ahí, sus tests en `tests/`, y su llamada en `cli.py::run`.

## Antes de mandar un PR

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
ruff check .
pytest
```

- Cualquier check nuevo o corregido necesita sus propios tests, tanto un
  caso que debe marcarse como uno que no debe marcarse (falso positivo).
- Los tests de `ports.py` y `gpu.py` no pueden depender del hardware real
  de quien ejecuta la suite (ni CI ni el desarrollador tienen por qué
  tener una GPU) — usa sockets reales de prueba para puertos y
  `monkeypatch` sobre `glob`/`shutil.which` para GPU, como ya hace el
  resto de la suite.
- `ruff check .` sin avisos.

## Reportar un falso positivo

El fragmento de `docker-compose.yml` concreto que lo dispara, no hace
falta el proyecto entero.
