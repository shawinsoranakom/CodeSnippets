def test_reserve_container_port(self, docker_client, set_ports_check_image_alpine, protocol):
        if isinstance(docker_client, CmdDockerClient):
            pytest.skip("Running test only for one Docker executor")

        # reserve available container port
        port = reserve_available_container_port(duration=1, protocol=protocol)
        port = Port(port, protocol or "tcp")
        assert is_container_port_reserved(port)
        assert container_ports_can_be_bound(port)
        assert not is_port_available_for_containers(port)

        # reservation should fail immediately after
        with pytest.raises(PortNotAvailableException):
            reserve_container_port(port)

        # reservation should work after expiry time
        time.sleep(1)
        assert not is_container_port_reserved(port)
        assert is_port_available_for_containers(port)
        reserve_container_port(port, duration=1)
        assert is_container_port_reserved(port)
        assert container_ports_can_be_bound(port)

        # reservation should work on privileged port
        port = reserve_available_container_port(duration=1, port_start=1, port_end=1024)
        assert is_container_port_reserved(port)
        assert container_ports_can_be_bound(port)
        assert not is_port_available_for_containers(port)