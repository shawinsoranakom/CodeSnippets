def test_build_image(
        self, docker_client: ContainerClient, custom_context, dockerfile_as_dir, tmp_path, cleanups
    ):
        if custom_context and is_podman_test():
            # TODO: custom context currently failing with Podman
            pytest.skip("Test not applicable when run against Podman (only Docker)")

        dockerfile_dir = tmp_path / "dockerfile"
        tmp_file = short_uid()
        ctx_dir = tmp_path / "context" if custom_context else dockerfile_dir
        dockerfile_path = os.path.join(dockerfile_dir, "Dockerfile")
        dockerfile = f"""
        FROM alpine
        ADD {tmp_file} .
        ENV foo=bar
        EXPOSE 45329
        """
        save_file(dockerfile_path, dockerfile)
        save_file(os.path.join(ctx_dir, tmp_file), "test content 123")

        kwargs = {"context_path": str(ctx_dir)} if custom_context else {}
        dockerfile_ref = str(dockerfile_dir) if dockerfile_as_dir else dockerfile_path

        image_name = f"img-{short_uid()}"
        build_logs = docker_client.build_image(
            dockerfile_path=dockerfile_ref, image_name=image_name, **kwargs
        )
        # The exact log files are very different between the CMD and SDK
        # We just run some smoke tests
        assert build_logs
        assert isinstance(build_logs, str)
        assert "ADD" in build_logs

        cleanups.append(lambda: docker_client.remove_image(image_name, force=True))

        assert image_name in docker_client.get_docker_image_names()
        result = docker_client.inspect_image(image_name, pull=False)
        assert "foo=bar" in result["Config"]["Env"]
        assert "45329/tcp" in result["Config"]["ExposedPorts"]