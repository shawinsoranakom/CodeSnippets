def _run_python_code_in_docker(
        self,
        filename: str | Path,
        args: list[str],
        timeout: int = 120,
        env_vars: dict[str, str] | None = None,
    ) -> str:
        """Run a Python script in a Docker container

        Args:
            filename: Path to the Python file
            args: Command line arguments for the script
            timeout: Timeout in seconds
            env_vars: Environment variables to set

        Returns:
            str: The output of the script
        """
        file_path = self.workspace.get_path(filename)
        try:
            client = docker.from_env()
            image_name = "python:3-alpine"
            container_is_fresh = False
            container_name = self.config.docker_container_name
            with self.workspace.mount() as local_path:
                try:
                    container: DockerContainer = client.containers.get(
                        container_name
                    )  # type: ignore
                    # Remove existing container - it may have stale mounts from
                    # a previous run with a different workspace directory
                    logger.debug(
                        f"Removing existing container '{container_name}' "
                        "to refresh mount bindings"
                    )
                    container.remove(force=True)
                    raise NotFound("Container removed, recreating")
                except NotFound:
                    try:
                        client.images.get(image_name)
                        logger.debug(f"Image '{image_name}' found locally")
                    except ImageNotFound:
                        logger.info(
                            f"Image '{image_name}' not found locally,"
                            " pulling from Docker Hub..."
                        )
                        # Use the low-level API to stream the pull response
                        low_level_client = docker.APIClient()
                        for line in low_level_client.pull(
                            image_name, stream=True, decode=True
                        ):
                            # Print the status and progress, if available
                            status = line.get("status")
                            progress = line.get("progress")
                            if status and progress:
                                logger.info(f"{status}: {progress}")
                            elif status:
                                logger.info(status)

                    # Use timeout for container sleep duration
                    sleep_duration = str(max(timeout, 60))
                    logger.debug(f"Creating new {image_name} container...")
                    container: DockerContainer = client.containers.run(
                        image_name,
                        ["sleep", sleep_duration],
                        volumes={
                            str(local_path.resolve()): {
                                "bind": "/workspace",
                                "mode": "rw",
                            }
                        },
                        working_dir="/workspace",
                        stderr=True,
                        stdout=True,
                        detach=True,
                        name=container_name,
                        environment=env_vars or {},
                    )  # type: ignore
                    container_is_fresh = True

                if not container.status == "running":
                    container.start()
                elif not container_is_fresh:
                    container.restart()

                logger.debug(f"Running {file_path} in container {container.name}...")

                # Prepare environment for exec_run
                exec_env = env_vars or {}

                exec_result = container.exec_run(
                    [
                        "python",
                        "-B",
                        file_path.relative_to(self.workspace.root).as_posix(),
                    ]
                    + args,
                    stderr=True,
                    stdout=True,
                    environment=exec_env,
                )

                if exec_result.exit_code != 0:
                    raise CodeExecutionError(exec_result.output.decode("utf-8"))

                return exec_result.output.decode("utf-8")

        except DockerException as e:
            logger.warning(
                "Could not run the script in a container. "
                "If you haven't already, please install Docker: "
                "https://docs.docker.com/get-docker/"
            )
            raise CommandExecutionError(f"Could not run the script in a container: {e}")