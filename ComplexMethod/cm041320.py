def test_default_localstack_container_configurator(
    container_factory, wait_for_localstack_ready, tmp_path, monkeypatch, stream_container_logs
):
    volume = tmp_path / "localstack-volume"
    volume.mkdir(parents=True)

    # overwrite a few config variables
    from localstack import config

    monkeypatch.setenv("DEBUG", "1")
    monkeypatch.setenv("LOCALSTACK_AUTH_TOKEN", "")
    monkeypatch.setenv("LOCALSTACK_API_KEY", "")
    monkeypatch.setenv("ACTIVATE_PRO", "0")
    monkeypatch.setattr(config, "DEBUG", True)
    monkeypatch.setattr(config, "VOLUME_DIR", str(volume))
    monkeypatch.setattr(config, "DOCKER_FLAGS", "-p 23456:4566 -e MY_TEST_VAR=foobar")

    container: Container = container_factory()
    configure_container(container)

    stream_container_logs(container)
    wait_for_localstack_ready(container.start())

    # check startup works correctly
    response = requests.get("http://localhost:4566/_localstack/health")
    assert response.ok

    # check docker-flags was created correctly
    response = requests.get("http://localhost:23456/_localstack/health")
    assert response.ok, "couldn't reach localstack on port 23456 - does DOCKER_FLAGS work?"

    response = requests.get("http://localhost:4566/_localstack/diagnose")
    assert response.ok, "couldn't reach diagnose endpoint. is DEBUG=1 set?"
    diagnose = response.json()

    # a few smoke tests of important configs
    assert diagnose["config"]["GATEWAY_LISTEN"] == ["0.0.0.0:4566"]
    # check that docker-socket was mounted correctly
    assert diagnose["docker-inspect"], "was the docker socket mounted?"
    assert diagnose["docker-inspect"]["Config"]["Image"] == "localstack/localstack"
    assert diagnose["docker-inspect"]["Path"] == "docker-entrypoint.sh"
    assert {
        "Type": "bind",
        "Source": str(volume),
        "Destination": "/var/lib/localstack",
        "Mode": "",
        "RW": True,
        "Propagation": "rprivate",
    } in diagnose["docker-inspect"]["Mounts"]

    # from DOCKER_FLAGS
    assert "MY_TEST_VAR=foobar" in diagnose["docker-inspect"]["Config"]["Env"]

    # check that external service ports were mapped correctly
    ports = diagnose["docker-inspect"]["NetworkSettings"]["Ports"]
    for port in external_service_ports:
        assert ports[f"{port}/tcp"] == [{"HostIp": "127.0.0.1", "HostPort": f"{port}"}]