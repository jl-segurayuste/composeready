from composeready.checks import gpu


def test_service_without_gpu_request_is_clean():
    assert gpu.check("web", {}) == []


def test_legacy_runtime_nvidia_detected(monkeypatch):
    monkeypatch.setattr(gpu.glob, "glob", lambda pattern: [])
    monkeypatch.setattr(gpu.shutil, "which", lambda name: None)
    findings = gpu.check("web", {"runtime": "nvidia"})
    assert len(findings) == 1
    assert "/dev/nvidia" in findings[0].detail


def test_modern_deploy_syntax_detected_and_host_ready(monkeypatch):
    monkeypatch.setattr(gpu.glob, "glob", lambda pattern: ["/dev/nvidia0"])
    monkeypatch.setattr(gpu.shutil, "which", lambda name: "/usr/bin/nvidia-smi")
    service = {
        "deploy": {
            "resources": {
                "reservations": {"devices": [{"driver": "nvidia", "count": 1}]}
            }
        }
    }
    assert gpu.check("web", service) == []


def test_modern_deploy_syntax_host_missing_gpu(monkeypatch):
    monkeypatch.setattr(gpu.glob, "glob", lambda pattern: [])
    monkeypatch.setattr(gpu.shutil, "which", lambda name: None)
    service = {
        "deploy": {
            "resources": {
                "reservations": {"devices": [{"capabilities": ["gpu"]}]}
            }
        }
    }
    findings = gpu.check("web", service)
    assert len(findings) == 1
    assert "nvidia-smi" in findings[0].detail


def test_deploy_without_gpu_capability_ignored():
    service = {
        "deploy": {"resources": {"reservations": {"devices": [{"driver": "something-else"}]}}}
    }
    assert gpu.check("web", service) == []
