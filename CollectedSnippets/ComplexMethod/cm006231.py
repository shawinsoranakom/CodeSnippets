def create_app():
    """Create the FastAPI app and include the router."""
    from langflow.utils.version import get_version_info

    __version__ = get_version_info()["version"]
    configure()
    lifespan = get_lifespan(version=__version__)

    settings = get_settings_service().settings

    app = FastAPI(
        title="Langflow",
        version=__version__,
        lifespan=lifespan,
        root_path=settings.root_path,
    )
    app.add_middleware(
        ContentSizeLimitMiddleware,
    )

    setup_sentry(app)

    # Warn about future CORS changes
    warn_about_future_cors_changes(settings)

    # Configure CORS using settings (with backward compatible defaults)
    origins = settings.cors_origins
    if isinstance(origins, str) and origins != "*":
        origins = [origins]

    # Apply current CORS configuration (maintains backward compatibility)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )
    app.add_middleware(JavaScriptMIMETypeMiddleware)

    @app.middleware("http")
    async def check_boundary(request: Request, call_next):
        if "/api/v1/files/upload" in request.url.path:
            content_type = request.headers.get("Content-Type")

            if not content_type or "multipart/form-data" not in content_type or "boundary=" not in content_type:
                return JSONResponse(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    content={"detail": "Content-Type header must be 'multipart/form-data' with a boundary parameter."},
                )

            boundary = content_type.split("boundary=")[-1].strip()

            if not re.match(r"^[\w\-]{1,70}$", boundary):
                return JSONResponse(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    content={"detail": "Invalid boundary format"},
                )

            body = await request.body()

            boundary_start = f"--{boundary}".encode()
            # The multipart/form-data spec doesn't require a newline after the boundary, however many clients do
            # implement it that way
            boundary_end = f"--{boundary}--\r\n".encode()
            boundary_end_no_newline = f"--{boundary}--".encode()

            if not body.startswith(boundary_start) or not body.endswith((boundary_end, boundary_end_no_newline)):
                return JSONResponse(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    content={"detail": "Invalid multipart formatting"},
                )

        return await call_next(request)

    @app.middleware("http")
    async def forwarded_prefix_middleware(request: Request, call_next):
        """Honour X-Forwarded-Prefix set by a reverse proxy.

        When a reverse proxy (e.g. Nginx) strips a URL prefix before forwarding
        the request, it can advertise the original prefix via X-Forwarded-Prefix.
        We propagate this into the ASGI ``root_path`` so that transports like
        MCP SSE include the prefix in the POST-back URLs they hand to clients.

        This middleware is only active when ``root_path`` is configured in
        settings (i.e. the operator has explicitly opted into reverse-proxy
        mode).  The header value takes precedence over the static setting
        because the proxy is the runtime source of truth for the prefix.
        """
        if not settings.root_path:
            return await call_next(request)

        prefix = request.headers.get("X-Forwarded-Prefix", "").rstrip("/")
        if prefix and prefix.startswith("/") and "://" not in prefix and "?" not in prefix and "#" not in prefix:
            request.scope["root_path"] = prefix
        return await call_next(request)

    @app.middleware("http")
    async def flatten_query_string_lists(request: Request, call_next):
        flattened: list[tuple[str, str]] = []
        for key, value in request.query_params.multi_items():
            flattened.extend((key, entry) for entry in value.split(","))

        request.scope["query_string"] = urlencode(flattened, doseq=True).encode("utf-8")

        return await call_next(request)

    if prome_port_str := os.environ.get("LANGFLOW_PROMETHEUS_PORT"):
        # set here for create_app() entry point
        prome_port = int(prome_port_str)
        if prome_port > 0 or prome_port < MAX_PORT:
            logger.debug(f"Starting Prometheus server on port {prome_port}...")
            settings.prometheus_enabled = True
            settings.prometheus_port = prome_port
        else:
            msg = f"Invalid port number {prome_port_str}"
            raise ValueError(msg)

    if settings.prometheus_enabled:
        from prometheus_client import start_http_server

        start_http_server(settings.prometheus_port)

    if settings.mcp_server_enabled:
        from langflow.api.v1 import mcp_router

        router.include_router(mcp_router)

    app.include_router(router)
    app.include_router(health_check_router)
    app.include_router(log_router)

    # Discover and register additional routers from plugins (langflow.plugins entry-point)
    load_plugin_routes(app)

    @app.exception_handler(Exception)
    async def exception_handler(_request: Request, exc: Exception):
        if isinstance(exc, HTTPException):
            await logger.aerror(f"HTTPException: {exc}", exc_info=exc)
            return JSONResponse(
                status_code=exc.status_code,
                content={"message": str(exc.detail)},
            )
        await logger.aerror(f"unhandled error: {exc}", exc_info=exc)

        await log_exception_to_telemetry(exc, "handler")

        return JSONResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            content={"message": str(exc)},
        )

    FastAPIInstrumentor.instrument_app(app)

    add_pagination(app)

    return app