async def async_enable_logging(
    hass: core.HomeAssistant,
    verbose: bool = False,
    log_rotate_days: int | None = None,
    log_file: str | None = None,
    log_no_color: bool = False,
) -> None:
    """Set up the logging.

    This method must be run in the event loop.
    """
    fmt = (
        "%(asctime)s.%(msecs)03d %(levelname)s (%(threadName)s) [%(name)s] %(message)s"
    )

    if not log_no_color:
        try:
            from colorlog import ColoredFormatter  # noqa: PLC0415

            # basicConfig must be called after importing colorlog in order to
            # ensure that the handlers it sets up wraps the correct streams.
            logging.basicConfig(level=logging.INFO)

            colorfmt = f"%(log_color)s{fmt}%(reset)s"
            logging.getLogger().handlers[0].setFormatter(
                ColoredFormatter(
                    colorfmt,
                    datefmt=FORMAT_DATETIME,
                    reset=True,
                    log_colors={
                        "DEBUG": "cyan",
                        "INFO": "green",
                        "WARNING": "yellow",
                        "ERROR": "red",
                        "CRITICAL": "red",
                    },
                )
            )
        except ImportError:
            pass

    # If the above initialization failed for any reason, setup the default
    # formatting.  If the above succeeds, this will result in a no-op.
    logging.basicConfig(format=fmt, datefmt=FORMAT_DATETIME, level=logging.INFO)

    # Capture warnings.warn(...) and friends messages in logs.
    # The standard destination for them is stderr, which may end up unnoticed.
    # This way they're where other messages are, and can be filtered as usual.
    logging.captureWarnings(True)

    # Suppress overly verbose logs from libraries that aren't helpful
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("aiohttp.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    sys.excepthook = lambda *args: logging.getLogger().exception(
        "Uncaught exception", exc_info=args
    )
    threading.excepthook = lambda args: logging.getLogger().exception(
        "Uncaught thread exception",
        exc_info=(  # type: ignore[arg-type]
            args.exc_type,
            args.exc_value,
            args.exc_traceback,
        ),
    )

    logger = logging.getLogger()
    logger.setLevel(logging.INFO if verbose else logging.WARNING)

    if log_file is None:
        default_log_path = hass.config.path(ERROR_LOG_FILENAME)
        if "SUPERVISOR" in os.environ and "HA_DUPLICATE_LOG_FILE" not in os.environ:
            # Rename the default log file if it exists, since previous versions created
            # it even on Supervisor
            def rename_old_file() -> None:
                """Rename old log file in executor."""
                if os.path.isfile(default_log_path):
                    with contextlib.suppress(OSError):
                        os.rename(default_log_path, f"{default_log_path}.old")

            await hass.async_add_executor_job(rename_old_file)
            err_log_path = None
        else:
            err_log_path = default_log_path
    else:
        err_log_path = os.path.abspath(log_file)

    if err_log_path:
        err_handler = await hass.async_add_executor_job(
            _create_log_file, err_log_path, log_rotate_days
        )

        err_handler.setFormatter(logging.Formatter(fmt, datefmt=FORMAT_DATETIME))
        logger.addHandler(err_handler)

        # Save the log file location for access by other components.
        hass.data[DATA_LOGGING] = err_log_path

    async_activate_log_queue_handler(hass)