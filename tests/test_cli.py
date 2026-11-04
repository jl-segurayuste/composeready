from pathlib import Path

from composeready.cli import main

FIXTURES = Path(__file__).parent / "fixtures"


def test_cli_flags_missing_bind_mount(capsys):
    code = main([str(FIXTURES / "docker-compose.yml")])
    out = capsys.readouterr().out
    assert code == 1
    assert "missing-dir" in out


def test_cli_clean_compose(tmp_path, capsys):
    f = tmp_path / "docker-compose.yml"
    f.write_text("services:\n  web:\n    image: nginx\n")
    code = main([str(f)])
    out = capsys.readouterr().out
    assert code == 0
    assert "listo" in out


def test_cli_missing_file_exits_2():
    assert main(["/does/not/exist"]) == 2


def test_cli_finds_compose_in_directory(tmp_path):
    (tmp_path / "compose.yaml").write_text("services:\n  web:\n    image: nginx\n")
    assert main([str(tmp_path)]) == 0


def test_cli_skip_flag(capsys):
    code = main([str(FIXTURES / "docker-compose.yml"), "--skip", "bind_mount", "--skip", "port"])
    assert code == 0


def test_cli_yaml_invalido_sale_2_sin_traza(tmp_path, capsys):
    (tmp_path / "compose.yml").write_text("services:\n  a: [\n")
    assert main([str(tmp_path)]) == 2
    assert "no se pudo leer" in capsys.readouterr().err
