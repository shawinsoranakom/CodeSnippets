def test_container_port_can_be_bound(
        self, docker_client, set_ports_check_image_alpine, protocol
    ):
        if isinstance(docker_client, CmdDockerClient):
            pytest.skip("Running test only for one Docker executor")

        # reserve available container port
        port = reserve_available_container_port(duration=1)
        start_time = datetime.datetime.now()
        assert container_ports_can_be_bound(port)
        assert not is_port_available_for_containers(port)

        # run test container with port exposed
        ports = PortMappings()
        ports.add(port, port)
        name = f"c-{short_uid()}"
        docker_client.run_container(
            "alpine",
            name=name,
            command=["sleep", "5"],
            entrypoint="",
            ports=ports,
            detach=True,
        )
        # assert that port can no longer be bound by new containers
        assert not container_ports_can_be_bound(port)

        # remove container, assert that port can be bound again
        docker_client.remove_container(name, force=True)
        assert container_ports_can_be_bound(port)
        delta = (datetime.datetime.now() - start_time).total_seconds()
        if delta <= 1:
            time.sleep(1.01 - delta)
        assert is_port_available_for_containers(port)