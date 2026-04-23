def test_list_containers_with_podman_image_ref_format(
        self, docker_client: ContainerClient, create_container, cleanups, monkeypatch
    ):
        # create custom image tag
        image_name = f"alpine:tag-{short_uid()}"
        _pull_image_if_not_exists(docker_client, "alpine")
        docker_client.tag_image("alpine", image_name)
        cleanups.append(lambda: docker_client.remove_image(image_name))

        # apply patch to simulate podman behavior
        container_init_orig = Container.__init__

        def container_init(self, attrs=None, *args, **kwargs):
            # Simulate podman API response, Docker returns "sha:..." for Image, podman returns "<image-name>:<tag>".
            #  See https://github.com/containers/podman/issues/8329
            attrs["Image"] = image_name
            container_init_orig(self, *args, attrs=attrs, **kwargs)

        monkeypatch.setattr(Container, "__init__", container_init)

        # start a container from the custom image tag
        c1 = create_container(image_name, command=["sleep", "3"])
        docker_client.start_container(c1.container_id, attach=False)

        # list containers, assert that container is contained in the list
        container_list = docker_client.list_containers()
        running_containers = [cnt for cnt in container_list if cnt["status"] == "running"]
        assert running_containers
        container_names = [info["name"] for info in container_list]
        assert c1.container_name in container_names

        # assert that get_running_container_names(..) call is successful as well
        container_names = docker_client.get_running_container_names()
        assert len(running_containers) == len(container_names)
        assert c1.container_name in container_names