def test_common_container_fixture_configurators(
    container_factory, wait_for_localstack_ready, tmp_path
):
    volume = tmp_path / "localstack-volume"
    volume.mkdir(parents=True)

    container: Container = container_factory(
        configurators=[
            ContainerConfigurators.random_container_name,
            ContainerConfigurators.random_gateway_port,
            ContainerConfigurators.random_service_port_range(20),
            ContainerConfigurators.debug,
            ContainerConfigurators.mount_docker_socket,
            ContainerConfigurators.mount_localstack_volume(volume),
            ContainerConfigurators.env_vars(
                {
                    "FOOBAR": "foobar",
                    "MY_TEST_ENV": "test",
                }
            ),
        ]
    )

    running_container = container.start()
    wait_for_localstack_ready(running_container)
    url = get_gateway_url(container)

    # port was exposed correctly
    response = requests.get(f"{url}/_localstack/health")
    assert response.ok

    # volume was mounted and directories were created correctly
    assert (volume / "cache" / "machine.json").exists()

    inspect = running_container.inspect()
    # volume was mounted correctly
    assert {
        "Type": "bind",
        "Source": str(volume),
        "Destination": "/var/lib/localstack",
        "Mode": "",
        "RW": True,
        "Propagation": "rprivate",
    } in inspect["Mounts"]
    # docker socket was mounted correctly
    assert {
        "Type": "bind",
        "Source": "/var/run/docker.sock",
        "Destination": "/var/run/docker.sock",
        "Mode": "",
        "RW": True,
        "Propagation": "rprivate",
    } in inspect["Mounts"]

    # debug was set
    assert "DEBUG=1" in inspect["Config"]["Env"]
    # environment variables were set
    assert "FOOBAR=foobar" in inspect["Config"]["Env"]
    assert "MY_TEST_ENV=test" in inspect["Config"]["Env"]
    # container name was set
    assert f"MAIN_CONTAINER_NAME={container.config.name}" in inspect["Config"]["Env"]