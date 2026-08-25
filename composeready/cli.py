from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .checks import bind_mounts, gpu, ports
from .compose import find_compose_file, iter_services, load_compose
from .finding import Finding


def run(compose_path: Path, skip: set[str]) -> list[Finding]:
    data = load_compose(compose_path)
    compose_dir = compose_path.parent
    findings: list[Finding] = []

    for name, service in iter_services(data):
        if "bind_mount" not in skip:
            findings.extend(bind_mounts.check(name, service, compose_dir))
        if "port" not in skip:
            findings.extend(ports.check(name, service))
        if "gpu" not in skip:
            findings.extend(gpu.check(name, service))

    return findings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="composeready",
        description=(
            "Comprueba si el host real cumple lo que un docker-compose asume "
            "(rutas de bind-mount, puertos libres, GPU) antes de levantarlo."
        ),
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Fichero compose o directorio que lo contiene (por defecto: directorio actual)",
    )
    parser.add_argument(
        "--skip",
        action="append",
        choices=["bind_mount", "port", "gpu"],
        default=[],
        help="Check a omitir (repetible)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    compose_path = find_compose_file(Path(args.path))
    if compose_path is None:
        print(f"composeready: no se encontró ningún fichero compose en '{args.path}'", file=sys.stderr)
        return 2

    findings = run(compose_path, set(args.skip))

    if not findings:
        print(f"composeready: {compose_path} — listo, el host cumple lo que asume.")
        return 0

    for f in findings:
        print(f.format())
    print(f"\n{len(findings)} problema(s) encontrado(s) antes de arrancar.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
