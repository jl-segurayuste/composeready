import socket

from composeready.checks.ports import check


def _free_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("0.0.0.0", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def test_flags_port_already_bound():
    port = _free_port()
    holder = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    holder.bind(("0.0.0.0", port))
    holder.listen(1)
    try:
        findings = check("web", {"ports": [f"{port}:80"]})
        assert len(findings) == 1
        assert str(port) in findings[0].message
    finally:
        holder.close()


def test_does_not_flag_free_port():
    port = _free_port()
    findings = check("web", {"ports": [f"{port}:80"]})
    assert findings == []


def test_ignores_container_only_port():
    assert check("web", {"ports": [80]}) == []


def test_ignores_udp():
    port = _free_port()
    holder = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    holder.bind(("0.0.0.0", port))
    try:
        findings = check("web", {"ports": [f"{port}:80/udp"]})
        assert findings == []
    finally:
        holder.close()


def test_ignores_port_ranges():
    assert check("web", {"ports": ["8080-8090:80-90"]}) == []


def test_long_form():
    port = _free_port()
    holder = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    holder.bind(("0.0.0.0", port))
    holder.listen(1)
    try:
        findings = check("web", {"ports": [{"published": port, "target": 80, "protocol": "tcp"}]})
        assert len(findings) == 1
    finally:
        holder.close()


def test_no_ports_key():
    assert check("web", {}) == []


def test_flags_port_from_variable_default_and_dotenv(tmp_path):
    port = _free_port()
    holder = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    holder.bind(("0.0.0.0", port))
    holder.listen(1)
    try:
        assert len(check("web", {"ports": [f"${{WEB_PORT:-{port}}}:80"]}, env={})) == 1
        assert len(check("web", {"ports": ["${WEB_PORT}:80"]}, env={"WEB_PORT": str(port)})) == 1
        assert len(check("web", {"ports": [{"target": 80, "published": "${P}"}]}, env={"P": str(port)})) == 1

        from composeready.cli import run

        (tmp_path / ".env").write_text(f"WEB_PORT={port}\n")
        (tmp_path / "compose.yml").write_text('services:\n  w:\n    ports: ["${WEB_PORT:-1}:80"]\n')
        assert [f.check for f in run(tmp_path / "compose.yml", set())] == ["port"]
    finally:
        holder.close()
