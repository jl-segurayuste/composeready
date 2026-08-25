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
