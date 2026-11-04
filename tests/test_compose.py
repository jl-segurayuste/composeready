from composeready.compose import find_compose_file, iter_services, load_compose, resolve_env


def test_resolve_env_with_default():
    assert resolve_env("${FOO:-bar}", env={}) == "bar"


def test_resolve_env_from_environment():
    assert resolve_env("${FOO}", env={"FOO": "baz"}) == "baz"


def test_resolve_env_bare_dollar():
    assert resolve_env("$FOO/data", env={"FOO": "/srv"}) == "/srv/data"


def test_resolve_env_leaves_undefined_literal():
    assert resolve_env("${UNSET_VAR}", env={}) == "${UNSET_VAR}"


def test_iter_services_skips_non_dict_entries():
    data = {"services": {"web": {"image": "nginx"}, "broken": "not-a-dict"}}
    assert iter_services(data) == [("web", {"image": "nginx"})]


def test_iter_services_no_services_key():
    assert iter_services({}) == []


def test_find_compose_file_direct(tmp_path):
    f = tmp_path / "docker-compose.yml"
    f.write_text("services: {}\n")
    assert find_compose_file(f) == f


def test_find_compose_file_in_directory(tmp_path):
    f = tmp_path / "compose.yaml"
    f.write_text("services: {}\n")
    assert find_compose_file(tmp_path) == f


def test_find_compose_file_missing(tmp_path):
    assert find_compose_file(tmp_path) is None


def test_load_compose_non_dict_yaml(tmp_path):
    f = tmp_path / "weird.yml"
    f.write_text("- just\n- a\n- list\n")
    assert load_compose(f) == {}


def test_resolve_env_colon_default_with_empty_value():
    assert resolve_env("${FOO:-bar}", env={"FOO": ""}) == "bar"
    assert resolve_env("${FOO-bar}", env={"FOO": ""}) == ""


def test_project_env_reads_dotenv_and_environment_wins(tmp_path, monkeypatch):
    from composeready.compose import project_env

    (tmp_path / ".env").write_text('# c\nWEB_PORT=9000\nexport DATA="./d"\nOTRA=1 # nota\n')
    monkeypatch.setenv("OTRA", "2")
    env = project_env(tmp_path)
    assert env["WEB_PORT"] == "9000" and env["DATA"] == "./d" and env["OTRA"] == "2"


def test_find_compose_file_mismo_orden_que_docker(tmp_path):
    from composeready.compose import find_compose_file

    for name in ("docker-compose.yml", "compose.yml", "compose.yaml"):
        (tmp_path / name).write_text("services: {}\n")
    assert find_compose_file(tmp_path).name == "compose.yaml"
