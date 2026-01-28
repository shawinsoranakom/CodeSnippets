def configure_logging(force_cloud_logging: bool = False) -> None:
    """Configure the native logging module based on the LoggingConfig settings.

    This function sets up logging handlers and formatters according to the
    configuration specified in the LoggingConfig object. It supports various
    logging outputs including console, file, cloud, and JSON logging.

    The function uses the LoggingConfig object to determine which logging
    features to enable and how to configure them. This includes setting
    log levels, log formats, and output destinations.

    No arguments are required as the function creates its own LoggingConfig
    instance internally.

    Note: This function is typically called at the start of the application
    to set up the logging infrastructure.
    """
    config = LoggingConfig()
    log_handlers: list[logging.Handler] = []

    structured_logging = config.enable_cloud_logging or force_cloud_logging

    # Console output handlers
    if not structured_logging:
        stdout = logging.StreamHandler(stream=sys.stdout)
        stdout.setLevel(config.level)
        stdout.addFilter(BelowLevelFilter(logging.WARNING))
        if config.level == logging.DEBUG:
            stdout.setFormatter(AGPTFormatter(DEBUG_LOG_FORMAT))
        else:
            stdout.setFormatter(AGPTFormatter(SIMPLE_LOG_FORMAT))

        stderr = logging.StreamHandler()
        stderr.setLevel(logging.WARNING)
        if config.level == logging.DEBUG:
            stderr.setFormatter(AGPTFormatter(DEBUG_LOG_FORMAT))
        else:
            stderr.setFormatter(AGPTFormatter(SIMPLE_LOG_FORMAT))

        log_handlers += [stdout, stderr]

    # Cloud logging setup
    else:
        # Use Google Cloud Structured Log Handler. Log entries are printed to stdout
        # in a JSON format which is automatically picked up by Google Cloud Logging.
        from google.cloud.logging.handlers import StructuredLogHandler

        structured_log_handler = StructuredLogHandler(stream=sys.stdout)
        structured_log_handler.setLevel(config.level)
        log_handlers.append(structured_log_handler)

    # File logging setup
    if config.enable_file_logging:
        # create log directory if it doesn't exist
        if not config.log_dir.exists():
            config.log_dir.mkdir(parents=True, exist_ok=True)

        print(f"Log directory: {config.log_dir}")

        # Activity log handler (INFO and above)
        # Security fix: Use RotatingFileHandler with size limits to prevent disk exhaustion
        activity_log_handler = RotatingFileHandler(
            config.log_dir / LOG_FILE,
            mode="a",
            encoding="utf-8",
            maxBytes=10 * 1024 * 1024,  # 10MB per file
            backupCount=3,  # Keep 3 backup files (40MB total)
        )
        activity_log_handler.setLevel(config.level)
        activity_log_handler.setFormatter(
            AGPTFormatter(SIMPLE_LOG_FORMAT, no_color=True)
        )
        log_handlers.append(activity_log_handler)

        if config.level == logging.DEBUG:
            # Debug log handler (all levels)
            # Security fix: Use RotatingFileHandler with size limits
            debug_log_handler = RotatingFileHandler(
                config.log_dir / DEBUG_LOG_FILE,
                mode="a",
                encoding="utf-8",
                maxBytes=10 * 1024 * 1024,  # 10MB per file
                backupCount=3,  # Keep 3 backup files (40MB total)
            )
            debug_log_handler.setLevel(logging.DEBUG)
            debug_log_handler.setFormatter(
                AGPTFormatter(DEBUG_LOG_FORMAT, no_color=True)
            )
            log_handlers.append(debug_log_handler)

        # Error log handler (ERROR and above)
        # Security fix: Use RotatingFileHandler with size limits
        error_log_handler = RotatingFileHandler(
            config.log_dir / ERROR_LOG_FILE,
            mode="a",
            encoding="utf-8",
            maxBytes=10 * 1024 * 1024,  # 10MB per file
            backupCount=3,  # Keep 3 backup files (40MB total)
        )
        error_log_handler.setLevel(logging.ERROR)
        error_log_handler.setFormatter(AGPTFormatter(DEBUG_LOG_FORMAT, no_color=True))
        log_handlers.append(error_log_handler)

    # Configure the root logger
    logging.basicConfig(
        format=(
            "%(levelname)s  %(message)s"
            if structured_logging
            else (
                DEBUG_LOG_FORMAT if config.level == logging.DEBUG else SIMPLE_LOG_FORMAT
            )
        ),
        level=config.level,
        handlers=log_handlers,
    )
