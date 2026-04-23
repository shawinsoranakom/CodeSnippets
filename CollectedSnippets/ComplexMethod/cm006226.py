def run(
    *,
    host: str | None = typer.Option(None, help="Host to bind the server to.", show_default=False),
    workers: int | None = typer.Option(None, help="Number of worker processes.", show_default=False),
    worker_timeout: int | None = typer.Option(None, help="Worker timeout in seconds.", show_default=False),
    port: int | None = typer.Option(None, help="Port to listen on.", show_default=False),
    components_path: Path | None = typer.Option(
        Path(__file__).parent / "components",
        help="Path to the directory containing custom components.",
        show_default=False,
    ),
    # .env file param
    env_file: Path | None = typer.Option(
        None,
        help="Path to the .env file containing environment variables.",
        show_default=False,
    ),
    log_level: str | None = typer.Option(
        None,
        help="Logging level. One of: [debug, info, warning, error, critical]. Defaults to info.",
        show_default=False,
    ),
    log_file: Path | None = typer.Option(None, help="Path to the log file.", show_default=False),
    log_rotation: str | None = typer.Option(None, help="Log rotation(Time/Size).", show_default=False),
    cache: str | None = typer.Option(  # noqa: ARG001
        None,
        help="Type of cache to use. (InMemoryCache, SQLiteCache)",
        show_default=False,
    ),
    dev: bool | None = typer.Option(None, help="Run in development mode (may contain bugs)", show_default=False),  # noqa: ARG001
    frontend_path: str | None = typer.Option(
        None,
        help="Path to the frontend directory containing build files. This is for development purposes only.",
        show_default=False,
    ),
    open_browser: bool | None = typer.Option(
        None,
        help="Open the browser after starting the server.",
        show_default=False,
    ),
    remove_api_keys: bool | None = typer.Option(  # noqa: ARG001
        None,
        help="Remove API keys from the projects saved in the database.",
        show_default=False,
    ),
    backend_only: bool | None = typer.Option(
        None,
        help="Run only the backend server without the frontend.",
        show_default=False,
    ),
    store: bool | None = typer.Option(  # noqa: ARG001
        None,
        help="Enables the store features.",
        show_default=False,
    ),
    auto_saving: bool | None = typer.Option(  # noqa: ARG001
        None,
        help="Defines if the auto save is enabled.",
        show_default=False,
    ),
    auto_saving_interval: int | None = typer.Option(  # noqa: ARG001
        None,
        help="Defines the debounce time for the auto save.",
        show_default=False,
    ),
    health_check_max_retries: bool | None = typer.Option(  # noqa: ARG001
        None,
        help="Defines the number of retries for the health check.",
        show_default=False,
    ),
    max_file_size_upload: int | None = typer.Option(  # noqa: ARG001
        None,
        help="Defines the maximum file size for the upload in MB.",
        show_default=False,
    ),
    webhook_polling_interval: int | None = typer.Option(  # noqa: ARG001
        None,
        help="Defines the polling interval for the webhook.",
        show_default=False,
    ),
    ssl_cert_file_path: str | None = typer.Option(
        None, help="Defines the SSL certificate file path.", show_default=False
    ),
    ssl_key_file_path: str | None = typer.Option(None, help="Defines the SSL key file path.", show_default=False),
) -> None:
    """Run Langflow."""
    if env_file:
        if is_settings_service_initialized():
            err = (
                "Settings service is already initialized. This indicates potential race conditions "
                "with settings initialization. Ensure the settings service is not created during "
                "module loading."
            )
            # i.e. ensures the env file is loaded before the settings service is initialized
            raise ValueError(err)
        load_dotenv(env_file, override=True)

    # Set and normalize log level, with precedence: cli > env > default
    log_level = (log_level or os.environ.get("LANGFLOW_LOG_LEVEL") or "info").lower()
    os.environ["LANGFLOW_LOG_LEVEL"] = log_level

    configure(log_level=log_level, log_file=log_file, log_rotation=log_rotation)

    # Create progress indicator (show verbose timing if log level is DEBUG)
    verbose = log_level == "debug"
    progress = create_langflow_progress(verbose=verbose)

    # Step 0: Initializing Langflow
    with progress.step(0):
        logger.debug(f"Loading config from file: '{env_file}'" if env_file else "No env_file provided.")
        set_var_for_macos_issue()
        settings_service = get_settings_service()

    # Step 1: Checking Environment
    with progress.step(1):
        for key, value in os.environ.items():
            new_key = key.replace("LANGFLOW_", "")
            if hasattr(settings_service.auth_settings, new_key):
                setattr(settings_service.auth_settings, new_key, value)

        frame = inspect.currentframe()
        valid_args: list = []
        values: dict = {}
        if frame is not None:
            arguments, _, _, values = inspect.getargvalues(frame)
            valid_args = [arg for arg in arguments if values[arg] is not None]

        for arg in valid_args:
            if arg == "components_path":
                settings_service.settings.update_settings(components_path=components_path)
            elif hasattr(settings_service.settings, arg):
                settings_service.set(arg, values[arg])
            elif hasattr(settings_service.auth_settings, arg):
                settings_service.auth_settings.set(arg, values[arg])
            logger.debug("Loading config from cli parameter '%s'", arg)

        # Get final values from settings
        host = settings_service.settings.host
        port = settings_service.settings.port
        workers = settings_service.settings.workers
        worker_timeout = settings_service.settings.worker_timeout
        log_level = settings_service.settings.log_level
        frontend_path = settings_service.settings.frontend_path
        backend_only = settings_service.settings.backend_only
        ssl_cert_file_path = (
            settings_service.settings.ssl_cert_file if ssl_cert_file_path is None else ssl_cert_file_path
        )
        ssl_key_file_path = settings_service.settings.ssl_key_file if ssl_key_file_path is None else ssl_key_file_path

        # create path object if frontend_path is provided
        static_files_dir: Path | None = Path(frontend_path) if frontend_path else None

    # Step 2: Starting Core Services
    with progress.step(2):
        app = setup_app(static_files_dir=static_files_dir, backend_only=bool(backend_only))

    # Step 3: Connecting Database (this happens inside setup_app via dependencies)
    with progress.step(3):
        # Pre-flight: fail fast if PostgreSQL version is too old, before
        # spawning any server process (avoids messy lifespan / worker errors).
        database_url = settings_service.settings.database_url
        if database_url:
            try:
                check_postgresql_version_sync(database_url)
            except UnsupportedPostgreSQLVersionError:
                sys.exit(1)

        # check if port is being used
        if is_port_in_use(port, host):
            port = get_free_port(port)

        # Store the runtime-detected port in settings (temporary until strict port enforcement)
        get_settings_service().settings.runtime_port = port

        protocol = "https" if ssl_cert_file_path and ssl_key_file_path else "http"

    # Step 4: Loading Components (placeholder for components loading)
    with progress.step(4):
        pass  # Components are loaded during app startup

    # Step 5: Adding Starter Projects (placeholder for starter projects)
    if get_settings_service().settings.create_starter_projects:
        with progress.step(5):
            pass  # Starter projects are added during app startup

    # Step 6: Launching Langflow
    if platform.system() == "Windows":
        with progress.step(6):
            import uvicorn

            # Print summary and banner before starting the server, since uvicorn is a blocking call.
            # We _may_ be able to subprocess, but with window's spawn behavior, we'd have to move all
            # non-picklable code to the subprocess.
            progress.print_summary()
            print_banner(str(host), int(port or 7860), protocol)

        from langflow.helpers.windows_postgres_helper import LANGFLOW_DATABASE_URL, POSTGRESQL_PREFIXES

        db_url = os.environ.get(LANGFLOW_DATABASE_URL, "")
        loop_type = "asyncio"
        if (
            platform.system() == "Windows"
            and db_url
            and any(db_url.startswith(prefix) for prefix in POSTGRESQL_PREFIXES)
        ):
            loop_type = "none"  # Preserve pre-configured WindowsSelectorEventLoopPolicy

        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level=log_level,
            reload=False,
            workers=get_number_of_workers(workers),
            loop=loop_type,
        )
    else:
        with progress.step(6):
            # Use Gunicorn with LangflowUvicornWorker for non-Windows systems
            from langflow.server import LangflowApplication

            options = {
                "bind": f"{host}:{port}",
                "workers": get_number_of_workers(workers),
                "timeout": worker_timeout,
                "certfile": ssl_cert_file_path,
                "keyfile": ssl_key_file_path,
                "log_level": log_level.lower() if log_level is not None else "info",
                "preload_app": os.environ.get("LANGFLOW_GUNICORN_PRELOAD", "false").lower() == "true",
            }
            server = LangflowApplication(app, options)

            # Start the webapp process
            process_manager.webapp_process = Process(target=server.run)
            process_manager.webapp_process.start()

            wait_for_server_ready(host, port, protocol)

        # Print summary and banner after server is ready
        progress.print_summary()
        print_banner(str(host), int(port or 7860), protocol)

        # Handle browser opening
        if open_browser and not backend_only:
            click.launch(f"{protocol}://{host}:{port}")

        try:
            process_manager.webapp_process.join()
        except KeyboardInterrupt:
            # SIGINT should be handled by the signal handler, but leaving here for safety
            logger.warning("KeyboardInterrupt caught in main thread")
        finally:
            process_manager.shutdown()