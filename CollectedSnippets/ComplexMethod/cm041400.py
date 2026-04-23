def test_container_lifecycle_commands(self, docker_client: ContainerClient):
        container_name = _random_container_name()
        output = docker_client.create_container(
            "alpine",
            name=container_name,
            command=["sh", "-c", "for i in `seq 30`; do sleep 1; echo $i; done"],
        )
        container_id = output.strip()
        assert container_id

        try:
            docker_client.start_container(container_id)
            assert DockerContainerStatus.UP == docker_client.get_container_status(container_name)

            # consider different "paused" statuses for Docker / Podman
            docker_client.pause_container(container_id)
            expected_statuses = (DockerContainerStatus.PAUSED, DockerContainerStatus.DOWN)
            container_status = docker_client.get_container_status(container_name)
            assert container_status in expected_statuses

            docker_client.unpause_container(container_id)
            assert DockerContainerStatus.UP == docker_client.get_container_status(container_name)

            docker_client.restart_container(container_id)
            assert docker_client.get_container_status(container_name) == DockerContainerStatus.UP

            docker_client.stop_container(container_id)
            assert DockerContainerStatus.DOWN == docker_client.get_container_status(container_name)
        finally:
            docker_client.remove_container(container_id)

        assert DockerContainerStatus.NON_EXISTENT == docker_client.get_container_status(
            container_name
        )