def get_api_parser(exit_on_error: bool = True) -> ArgumentParser:
    """
    Creates and returns the argument parser used for:
        g4f api ...
    """
    api_parser = ArgumentParser(description="Run the API and GUI", exit_on_error=exit_on_error)

    api_parser.add_argument(
        "--bind",
        default=None,
        help=f"The bind address (default: 0.0.0.0:{DEFAULT_PORT})."
    )
    api_parser.add_argument(
        "--port", "-p",
        default=None,
        help=f"Port for the API server (default: {DEFAULT_PORT})."
    )
    api_parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="Enable verbose logging."
    )

    # Deprecated GUI flag but kept for compatibility
    api_parser.add_argument(
        "--gui", "-g",
        default=None,
        action="store_true",
        help="(deprecated) Use --no-gui instead."
    )

    api_parser.add_argument(
        "--no-gui", "-ng",
        default=False,
        action="store_true",
        help="Run API without the GUI."
    )

    api_parser.add_argument(
        "--model",
        default=None,
        help="Default model for chat completion (incompatible with reload/workers)."
    )

    # Providers for chat completion
    api_parser.add_argument(
        "--provider",
        choices=[p.__name__ for p in Provider.__providers__ if p.working],
        default=None,
        help="Default provider for chat completion."
    )

    # Providers for image generation
    api_parser.add_argument(
        "--media-provider",
        choices=[
            p.__name__ for p in Provider.__providers__
            if p.working and bool(getattr(p, "image_models", False))
        ],
        default=None,
        help="Default provider for image generation."
    )

    api_parser.add_argument(
        "--proxy",
        default=None,
        help="Default HTTP proxy."
    )

    api_parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Number of worker processes."
    )

    api_parser.add_argument(
        "--disable-colors",
        action="store_true",
        help="Disable colorized output."
    )

    api_parser.add_argument(
        "--ignore-cookie-files",
        action="store_true",
        help="Do not read .har or cookie files."
    )

    api_parser.add_argument(
        "--cookies-dir",
        type=str,
        default=None,
        help="Custom directory for cookies/HAR files (overrides default)."
    )

    api_parser.add_argument(
        "--g4f-api-key",
        type=str,
        default=None,
        help="Authentication key for your API."
    )

    api_parser.add_argument(
        "--ignored-providers",
        nargs="+",
        choices=[p.__name__ for p in Provider.__providers__ if p.working],
        default=[],
        help="Providers to ignore during request processing."
    )

    api_parser.add_argument(
        "--cookie-browsers",
        nargs="+",
        choices=[browser.__name__ for browser in cookies.BROWSERS],
        default=[],
        help="Browsers to fetch cookies from."
    )

    api_parser.add_argument("--reload", action="store_true", help="Enable hot reload.")
    api_parser.add_argument("--demo", action="store_true", help="Enable demo mode.")

    api_parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help="Default request timeout in seconds."
    )

    api_parser.add_argument(
        "--stream-timeout",
        type=int,
        default=DEFAULT_STREAM_TIMEOUT,
        help="Default streaming timeout in seconds."
    )

    api_parser.add_argument("--ssl-keyfile", type=str, default=None, help="SSL key file.")
    api_parser.add_argument("--ssl-certfile", type=str, default=None, help="SSL cert file.")
    api_parser.add_argument("--log-config", type=str, default=None, help="Path to log config.")
    api_parser.add_argument("--access-log", action="store_true", default=True, help="Enable access logging.")
    api_parser.add_argument("--no-access-log", dest="access_log", action="store_false", help="Disable access logging.")

    api_parser.add_argument(
        "--browser-port",
        type=int,
        help="Port for browser automation tool."
    )

    api_parser.add_argument(
        "--browser-host",
        type=str,
        default="127.0.0.1",
        help="Host for browser automation tool."
    )

    return api_parser