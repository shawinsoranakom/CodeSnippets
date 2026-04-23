def __init__(
        self,
        *,
        custom_image_name: Optional[str] = None,
        container_name: Optional[str] = None,
        auto_remove: bool = True,
        stop_container: bool = True,
        docker_env: Optional[Dict[str, str]] = None,
        expose_port: int = 8888,
        token: Optional[Union[str, GenerateToken]] = None,
        work_dir: Union[Path, str] = "/workspace",
        bind_dir: Optional[Union[Path, str]] = None,
    ):
        """Start a Jupyter kernel gateway server in a Docker container.

        Args:
            custom_image_name: Custom Docker image to use. If None, builds and uses bundled image.
            container_name: Name for the Docker container. Auto-generated if None.
            auto_remove: If True, container will be deleted when stopped.
            stop_container: If True, container stops on program exit or when context manager exits.
            docker_env: Additional environment variables for the container.
            expose_port: Port to expose for Jupyter connection.
            token: Authentication token. If GenerateToken, creates random token. Empty for no auth.
            work_dir: Working directory inside the container.
            bind_dir: Local directory to bind to container's work_dir.
        """
        # Generate container name if not provided
        container_name = container_name or f"autogen-jupyterkernelgateway-{uuid.uuid4()}"

        # Initialize Docker client
        client = docker.from_env()
        # Set up bind directory if specified
        self._bind_dir: Optional[Path] = None
        if bind_dir:
            self._bind_dir = Path(bind_dir) if isinstance(bind_dir, str) else bind_dir
            self._bind_dir.mkdir(exist_ok=True)
            os.chmod(bind_dir, 0o777)

        # Determine and prepare Docker image
        image_name = custom_image_name or "autogen-jupyterkernelgateway"
        if not custom_image_name:
            try:
                client.images.get(image_name)
            except docker.errors.ImageNotFound:
                # Build default image if not found
                here = Path(__file__).parent
                dockerfile = io.BytesIO(self.DEFAULT_DOCKERFILE.encode("utf-8"))
                logging.info(f"Building image {image_name}...")
                client.images.build(path=str(here), fileobj=dockerfile, tag=image_name)
                logging.info(f"Image {image_name} built successfully")
        else:
            # Verify custom image exists
            try:
                client.images.get(image_name)
            except docker.errors.ImageNotFound as err:
                raise ValueError(f"Custom image {image_name} does not exist") from err
        if docker_env is None:
            docker_env = {}
        if token is None:
            token = DockerJupyterServer.GenerateToken()
        # Set up authentication token
        self._token = secrets.token_hex(32) if isinstance(token, DockerJupyterServer.GenerateToken) else token

        # Prepare environment variables
        env = {"TOKEN": self._token}
        env.update(docker_env)

        # Define volume configuration if bind directory is specified
        volumes = {str(self._bind_dir): {"bind": str(work_dir), "mode": "rw"}} if self._bind_dir else None

        # Start the container
        container = client.containers.run(
            image_name,
            detach=True,
            auto_remove=auto_remove,
            environment=env,
            publish_all_ports=True,
            name=container_name,
            volumes=volumes,
            working_dir=str(work_dir),
        )

        # Wait for container to be ready
        self._wait_for_ready(container)

        # Store container information
        self._container = container
        self._port = int(container.ports[f"{expose_port}/tcp"][0]["HostPort"])
        self._container_id = container.id
        self._expose_port = expose_port

        if self._container_id is None:
            raise ValueError("Failed to obtain container id.")

        # Define cleanup function
        def cleanup() -> None:
            try:
                assert self._container_id is not None
                inner_container = client.containers.get(self._container_id)
                inner_container.stop()
            except docker.errors.NotFound:
                pass
            atexit.unregister(cleanup)

        # Register cleanup if container should be stopped automatically
        if stop_container:
            atexit.register(cleanup)

        self._cleanup_func = cleanup
        self._stop_container = stop_container