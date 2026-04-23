def configure(
    *,
    log_level: str | None = None,
    log_file: Path | None = None,
    disable: bool | None = False,
    log_env: str | None = None,
    log_format: str | None = None,
    log_rotation: str | None = None,
    cache: bool | None = None,
    output_file=None,
) -> None:
    """Configure the logger."""
    # Early-exit only if structlog is configured AND current min level matches the requested one.
    cfg = structlog.get_config() if structlog.is_configured() else {}
    wrapper_class = cfg.get("wrapper_class")
    current_min_level = getattr(wrapper_class, "min_level", None)
    if os.getenv("LANGFLOW_LOG_LEVEL", "").upper() in VALID_LOG_LEVELS and log_level is None:
        log_level = os.getenv("LANGFLOW_LOG_LEVEL")

    log_level_str = os.getenv("LANGFLOW_LOG_LEVEL", "ERROR")
    if log_level is not None:
        log_level_str = log_level

    requested_min_level = LOG_LEVEL_MAP.get(log_level_str.upper(), logging.ERROR)
    if current_min_level == requested_min_level:
        return

    if log_level is None:
        log_level = "ERROR"

    if log_file is None:
        env_log_file = os.getenv("LANGFLOW_LOG_FILE", "")
        log_file = Path(env_log_file) if env_log_file else None

    if log_env is None:
        log_env = os.getenv("LANGFLOW_LOG_ENV", "")

    # Get log format from env if not provided
    if log_format is None:
        log_format = os.getenv("LANGFLOW_LOG_FORMAT")

    # Configure processors based on environment
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    # Add callsite information only when LANGFLOW_DEV is set
    if DEV:
        processors.append(
            structlog.processors.CallsiteParameterAdder(
                parameters=[
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                    structlog.processors.CallsiteParameter.LINENO,
                ]
            )
        )

    processors.extend(
        [
            add_serialized,
            remove_exception_in_production,
            buffer_writer,
        ]
    )

    # Configure output based on environment
    if log_env.lower() == "container" or log_env.lower() == "container_json":
        processors.append(structlog.processors.JSONRenderer())
    elif log_env.lower() == "container_csv":
        # Include callsite fields in key order when DEV is enabled
        key_order = ["timestamp", "level", "event"]
        if DEV:
            key_order += ["filename", "func_name", "lineno"]

        processors.append(structlog.processors.KeyValueRenderer(key_order=key_order, drop_missing=True))
    else:
        # Use rich console for pretty printing based on environment variable
        log_stdout_pretty = os.getenv("LANGFLOW_PRETTY_LOGS", "true").lower() == "true"
        if log_stdout_pretty:
            # If custom format is provided, use KeyValueRenderer with custom format
            if log_format:
                processors.append(structlog.processors.KeyValueRenderer())
            else:
                processors.append(structlog.dev.ConsoleRenderer(colors=True))
        else:
            processors.append(structlog.processors.JSONRenderer())

    # Get numeric log level
    numeric_level = LOG_LEVEL_MAP.get(log_level.upper(), logging.ERROR)

    # Create wrapper class and attach the min level for later comparison
    wrapper_class = structlog.make_filtering_bound_logger(numeric_level)
    wrapper_class.min_level = numeric_level

    # Configure structlog
    # Default to stdout for backward compatibility, unless output_file is specified
    log_output_file = output_file if output_file is not None else sys.stdout

    structlog.configure(
        processors=processors,
        wrapper_class=wrapper_class,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=log_output_file)
        if not log_file
        else structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=cache if cache is not None else True,
    )

    # Set up file logging if needed
    if log_file:
        if not log_file.parent.exists():
            cache_dir = Path(user_cache_dir("langflow"))
            log_file = cache_dir / "langflow.log"

        # Parse rotation settings
        if log_rotation:
            # Handle rotation like "1 day", "100 MB", etc.
            max_bytes = 10 * 1024 * 1024  # Default 10MB
            if "MB" in log_rotation.upper():
                try:
                    # Look for pattern like "100 MB" (with space)
                    parts = log_rotation.split()
                    expected_parts = 2
                    if len(parts) >= expected_parts and parts[1].upper() == "MB":
                        mb = int(parts[0])
                        if mb > 0:  # Only use valid positive values
                            max_bytes = mb * 1024 * 1024
                except (ValueError, IndexError):
                    pass
        else:
            max_bytes = 10 * 1024 * 1024  # Default 10MB

        # Since structlog doesn't have built-in rotation, we'll use stdlib logging for file output
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=5,
        )
        file_handler.setFormatter(logging.Formatter("%(message)s"))

        # Add file handler to root logger
        logging.root.addHandler(file_handler)
        logging.root.setLevel(numeric_level)

    # Set up interceptors for uvicorn and gunicorn
    setup_uvicorn_logger()
    setup_gunicorn_logger()

    # Create the global logger instance
    global logger  # noqa: PLW0603
    logger = structlog.get_logger()

    if disable:
        # In structlog, we can set a very high filter level to effectively disable logging
        structlog.configure(
            wrapper_class=structlog.make_filtering_bound_logger(logging.CRITICAL),
        )

    logger.debug("Logger set up with log level: %s", log_level)