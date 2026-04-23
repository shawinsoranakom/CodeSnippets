def test_tag_image(self, docker_client: ContainerClient):
        if _is_podman_test() and isinstance(docker_client, SdkDockerClient):
            # TODO: Podman raises "normalizing image: normalizing name for compat API: invalid reference format"
            pytest.skip("Image tagging not fully supported using SDK client against Podman API")

        _pull_image_if_not_exists(docker_client, "alpine")
        img_refs = [
            "localstack_dummy_image",
            "localstack_dummy_image:latest",
            "localstack_dummy_image:test",
            "docker.io/localstack_dummy_image:test2",
            "example.com:4510/localstack_dummy_image:test3",
        ]
        try:
            for img_ref in img_refs:
                docker_client.tag_image("alpine", img_ref)
                images = docker_client.get_docker_image_names(strip_latest=":latest" not in img_ref)
                expected = img_ref.split("/")[-1] if len(img_ref.split(":")) < 3 else img_ref
                assert expected in images
        finally:
            for img_ref in img_refs:
                try:
                    docker_client.remove_image(img_ref)
                except Exception as e:
                    LOG.info("Unable to remove image '%s': %s", img_ref, e)