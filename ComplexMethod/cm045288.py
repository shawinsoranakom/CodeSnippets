def __init__(
        self,
        timeout: int = 60,
        work_dir: Optional[Union[Path, str]] = None,
        functions: Sequence[
            Union[
                FunctionWithRequirements[Any, A],
                Callable[..., Any],
                FunctionWithRequirementsStr,
            ]
        ] = [],
        functions_module: str = "functions",
        cleanup_temp_files: bool = True,
        virtual_env_context: Optional[SimpleNamespace] = None,
    ):
        # Issue warning about using LocalCommandLineCodeExecutor
        warnings.warn(
            "Using LocalCommandLineCodeExecutor may execute code on the local machine which can be unsafe. "
            "For security, it is recommended to use DockerCommandLineCodeExecutor instead. "
            "To install Docker, visit: https://docs.docker.com/get-docker/",
            UserWarning,
            stacklevel=2,
        )

        if timeout < 1:
            raise ValueError("Timeout must be greater than or equal to 1.")
        self._timeout = timeout

        self._work_dir: Optional[Path] = None
        if work_dir is not None:
            # Check if user provided work_dir is the current directory and warn if so.
            if Path(work_dir).resolve() == Path.cwd().resolve():
                warnings.warn(
                    "Using the current directory as work_dir is deprecated.",
                    DeprecationWarning,
                    stacklevel=2,
                )
            if isinstance(work_dir, str):
                self._work_dir = Path(work_dir)
            else:
                self._work_dir = work_dir
            self._work_dir.mkdir(exist_ok=True)

        self._functions = functions
        # Setup could take some time so we intentionally wait for the first code block to do it.
        if len(functions) > 0:
            self._setup_functions_complete = False
        else:
            self._setup_functions_complete = True

        if not functions_module.isidentifier():
            raise ValueError("Module name must be a valid Python identifier")
        self._functions_module = functions_module

        self._cleanup_temp_files = cleanup_temp_files
        self._virtual_env_context: Optional[SimpleNamespace] = virtual_env_context

        self._temp_dir: Optional[tempfile.TemporaryDirectory[str]] = None
        self._started = False

        # Check the current event loop policy if on windows.
        if sys.platform == "win32":
            current_policy = asyncio.get_event_loop_policy()
            if hasattr(asyncio, "WindowsProactorEventLoopPolicy") and not isinstance(
                current_policy, asyncio.WindowsProactorEventLoopPolicy
            ):
                warnings.warn(
                    "The current event loop policy is not WindowsProactorEventLoopPolicy. "
                    "This may cause issues with subprocesses. "
                    "Try setting the event loop policy to WindowsProactorEventLoopPolicy. "
                    "For example: `asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())`. "
                    "See https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.ProactorEventLoop.",
                    stacklevel=2,
                )