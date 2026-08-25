from composeready.checks.bind_mounts import check


def test_flags_missing_relative_path(tmp_path):
    service = {"volumes": ["./data:/app/data"]}
    findings = check("web", service, tmp_path)
    assert len(findings) == 1
    assert "./data" in findings[0].message


def test_does_not_flag_existing_path(tmp_path):
    (tmp_path / "data").mkdir()
    service = {"volumes": ["./data:/app/data"]}
    findings = check("web", service, tmp_path)
    assert findings == []


def test_ignores_named_volumes(tmp_path):
    service = {"volumes": ["mydata:/app/data"]}
    findings = check("web", service, tmp_path)
    assert findings == []


def test_flags_missing_absolute_path(tmp_path):
    service = {"volumes": ["/does/not/exist:/app/data:ro"]}
    findings = check("web", service, tmp_path)
    assert len(findings) == 1


def test_long_form_bind_missing(tmp_path):
    service = {
        "volumes": [
            {"type": "bind", "source": "/does/not/exist", "target": "/app/data"},
        ]
    }
    findings = check("web", service, tmp_path)
    assert len(findings) == 1


def test_long_form_named_volume_ignored(tmp_path):
    service = {"volumes": [{"type": "volume", "source": "mydata", "target": "/app/data"}]}
    findings = check("web", service, tmp_path)
    assert findings == []


def test_env_var_expanded(tmp_path, monkeypatch):
    real = tmp_path / "real-data"
    real.mkdir()
    monkeypatch.setenv("DATA_DIR", str(real))
    service = {"volumes": ["${DATA_DIR}:/app/data"]}
    findings = check("web", service, tmp_path)
    assert findings == []


def test_no_volumes_key(tmp_path):
    assert check("web", {}, tmp_path) == []
