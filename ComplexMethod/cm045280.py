def __init__(
        self,
        image: str = "python:3-slim",
        container_name: Optional[str] = None,
        *,
        timeout: int = 60,
        work_dir: Union[Path, str, None] = None,
        bind_dir: Optional[Union[Path, str]] = None,
        auto_remove: bool = True,
        stop_container: bool = True,
        device_requests: Optional[List[DeviceRequest]] = None,
        functions: Sequence[
            Union[
                FunctionWithRequirements[Any, A],
                Callable[..., Any],
                FunctionWithRequirementsStr,
            ]
        ] = [],
        functions_module: str = "functions",
        extra_volumes: Optional[Dict[str, Dict[str, str]]] = None,
        extra_hosts: Optional[Dict[str, str]] = None,
        init_command: Optional[str] = None,
        delete_tmp_files: bool = False,
    ):
        if timeout < 1:
            raise ValueError("Timeout must be greater than or equal to 1.")

        # Handle working directory logic
        if work_dir is None:
            self._work_dir = None
        else:
            if isinstance(work_dir, str):
                work_dir = Path(work_dir)
            # Emit a deprecation warning if the user is using the current directory as working directory
            if work_dir.resolve() == Path.cwd().resolve():
                warnings.warn(
                    "Using the current directory as work_dir is deprecated.",
                    DeprecationWarning,
                    stacklevel=2,
                )
            self._work_dir = work_dir
            # Create the working directory if it doesn't exist
            self._work_dir.mkdir(exist_ok=True, parents=True)

        if container_name is None:
            self.container_name = f"autogen-code-exec-{uuid.uuid4()}"
        else:
            self.container_name = container_name

        self._timeout = timeout

        # Handle bind_dir
        self._bind_dir: Optional[Path] = None
        if bind_dir is not None:
            self._bind_dir = Path(bind_dir) if isinstance(bind_dir, str) else bind_dir
        else:
            self._bind_dir = self._work_dir  # Default to work_dir if not provided

        # Track temporary directory
        self._temp_dir: Optional[tempfile.TemporaryDirectory[str]] = None
        self._temp_dir_path: Optional[Path] = None

        self._started = False

        self._auto_remove = auto_remove
        self._stop_container = stop_container
        self._image = image

        if not functions_module.isidentifier():
            raise ValueError("Module name must be a valid Python identifier")

        self._functions_module = functions_module
        self._functions = functions
        self._extra_volumes = extra_volumes if extra_volumes is not None else {}
        self._extra_hosts = extra_hosts if extra_hosts is not None else {}
        self._init_command = init_command
        self._delete_tmp_files = delete_tmp_files
        self._device_requests = device_requests

        # Setup could take some time so we intentionally wait for the first code block to do it.
        if len(functions) > 0:
            self._setup_functions_complete = False
        else:
            self._setup_functions_complete = True

        self._container: Container | None = None
        self._running = False

        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._cancellation_futures: List[ConcurrentFuture[None]] = []