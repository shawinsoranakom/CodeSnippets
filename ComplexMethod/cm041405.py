def test_docker_image_names(self, docker_client: ContainerClient):
        try:
            docker_client.remove_image("alpine")
        except ContainerException:
            pass
        assert "alpine:latest" not in docker_client.get_docker_image_names()
        assert "alpine" not in docker_client.get_docker_image_names()
        docker_client.pull_image("alpine")
        assert "alpine:latest" in docker_client.get_docker_image_names()
        assert "alpine:latest" not in docker_client.get_docker_image_names(include_tags=False)
        assert "alpine" in docker_client.get_docker_image_names(include_tags=False)
        assert "alpine" in docker_client.get_docker_image_names()
        assert "alpine" not in docker_client.get_docker_image_names(strip_latest=False)