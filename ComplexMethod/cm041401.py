def test_list_containers_filter(self, docker_client: ContainerClient, create_container):
        name_prefix = "filter_tests_"
        cn1 = name_prefix + _random_container_name()
        cn2 = name_prefix + _random_container_name()
        cn3 = name_prefix + _random_container_name()

        c1 = create_container("alpine", name=cn1, command=["echo", "1"])
        c2 = create_container("alpine", name=cn2, command=["echo", "2"])
        c3 = create_container("alpine", name=cn3, command=["echo", "3"])

        # per id
        container_list = docker_client.list_containers(filter=f"id={c2.container_id}")
        assert 1 == len(container_list)
        assert c2.container_id.startswith(container_list[0]["id"])
        assert c2.container_name == container_list[0]["name"]
        # note: Docker returns "created", Podman returns "configured"
        assert container_list[0]["status"] in ["created", "configured"]

        # per name pattern
        container_list = docker_client.list_containers(filter=f"name={name_prefix}")
        assert 3 == len(container_list)
        image_names = [info["name"] for info in container_list]
        assert c1.container_name in image_names
        assert c2.container_name in image_names
        assert c3.container_name in image_names

        # multiple patterns
        container_list = docker_client.list_containers(
            filter=[
                f"id={c1.container_id}",
                f"name={container_name_prefix}",
            ]
        )
        assert 1 == len(container_list)
        assert c1.container_name == container_list[0]["name"]