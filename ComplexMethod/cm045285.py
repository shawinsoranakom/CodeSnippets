async def start(self) -> None:
        """(Experimental) Start the code executor.

        This method sets the working environment variables, connects to Docker and starts the code executor.
        If no working directory was provided to the code executor, it creates a temporary directory and sets it as the code executor working directory.
        """

        if self._work_dir is None and self._temp_dir is None:
            self._temp_dir = tempfile.TemporaryDirectory()
            self._temp_dir_path = Path(self._temp_dir.name)
            self._temp_dir_path.mkdir(exist_ok=True)

        # Start a container from the image, read to exec commands later
        try:
            client = docker.from_env()
        except DockerException as e:
            if "FileNotFoundError" in str(e):
                raise RuntimeError("Failed to connect to Docker. Please ensure Docker is installed and running.") from e
            raise
        except Exception as e:
            raise RuntimeError(f"Unexpected error while connecting to Docker: {str(e)}") from e

        # Check if the image exists
        try:
            await asyncio.to_thread(client.images.get, self._image)
        except ImageNotFound:
            # TODO logger
            logging.info(f"Pulling image {self._image}...")
            # Let the docker exception escape if this fails.
            await asyncio.to_thread(client.images.pull, self._image)

        # Prepare the command (if needed)
        shell_command = "/bin/sh"
        command = ["-c", f"{(self._init_command)};exec {shell_command}"] if self._init_command else None

        # Check if a container with the same name already exists and remove it
        try:
            existing_container = await asyncio.to_thread(client.containers.get, self.container_name)
            await asyncio.to_thread(existing_container.remove, force=True)
        except NotFound:
            pass

        self._container = await asyncio.to_thread(
            client.containers.create,
            self._image,
            name=self.container_name,
            entrypoint=shell_command,
            command=command,
            tty=True,
            detach=True,
            auto_remove=self._auto_remove,
            volumes={str(self.bind_dir.resolve()): {"bind": "/workspace", "mode": "rw"}, **self._extra_volumes},
            working_dir="/workspace",
            extra_hosts=self._extra_hosts,
            device_requests=self._device_requests,
        )
        await asyncio.to_thread(self._container.start)

        await _wait_for_ready(self._container)

        async def cleanup() -> None:
            await self.stop()
            asyncio_atexit.unregister(cleanup)  # type: ignore

        if self._stop_container:
            asyncio_atexit.register(cleanup)  # type: ignore

        # Check if the container is running
        if self._container.status != "running":
            logs_str = self._container.logs().decode("utf-8")
            raise ValueError(f"Failed to start container from image {self._image}. Logs: {logs_str}")

        self._loop = asyncio.get_running_loop()
        self._cancellation_futures = []
        logging.debug(f"Executor started, associated with event loop: {self._loop!r}")

        self._running = True