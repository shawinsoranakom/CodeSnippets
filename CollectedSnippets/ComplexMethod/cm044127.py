def main():
    """Start the OpenBB MCP server with enhanced FastAPI app import capabilities."""
    args = parse_args()
    mcp_service = MCPService()
    # Collect all command-line overrides from parsed args
    cli_overrides = args.uvicorn_config.copy()
    # Add MCP-specific CLI arguments if they exist
    if hasattr(args, "allowed_categories") and args.allowed_categories:
        cli_overrides["allowed_categories"] = args.allowed_categories

    if hasattr(args, "default_categories") and args.default_categories:
        cli_overrides["default_categories"] = args.default_categories

    if hasattr(args, "tool_discovery") and args.tool_discovery:
        cli_overrides["tool_discovery"] = args.tool_discovery

    if hasattr(args, "system_prompt") and args.system_prompt:
        cli_overrides["system_prompt"] = args.system_prompt

    if hasattr(args, "server_prompts") and args.server_prompts:
        cli_overrides["server_prompts"] = args.server_prompts

    # Load settings with proper priority order (CLI > env > config file > defaults)
    settings = mcp_service.load_with_overrides(**cli_overrides)

    try:
        # Use imported app if provided, otherwise default OpenBB app
        target_app = args.imported_app if args.imported_app else app

        # Extract runtime configuration from settings
        http_run_kwargs = settings.get_http_run_kwargs()
        httpx_kwargs = settings.get_httpx_kwargs()

        # Create MCP server with comprehensive configuration
        mcp_server = create_mcp_server(
            settings, target_app, httpx_kwargs, auth=settings.server_auth
        )

        if args.transport == "stdio":
            asyncio.run(stdio_main(mcp_server))
        else:
            cors_middleware = _build_runtime_middleware()

            # Start building arguments mcp.run
            run_kwargs = {
                "transport": args.transport,
                "middleware": cors_middleware,
            }

            # Extract uvicorn settings
            if http_run_kwargs.get("uvicorn_config"):
                uvicorn_config = http_run_kwargs["uvicorn_config"].copy()

                # Pop host and port to pass them as top-level args
                if "host" in uvicorn_config:
                    run_kwargs["host"] = uvicorn_config.pop("host")

                if "port" in uvicorn_config:
                    port = uvicorn_config.pop("port")
                    run_kwargs["port"] = int(port) if isinstance(port, str) else port

                # Pass the rest of the config in the nested dict.
                if uvicorn_config:
                    run_kwargs["uvicorn_config"] = uvicorn_config

            # Add SSE shutdown handling to middleware stack
            cors_middleware.append(Middleware(SSEShutdownWrapper))
            run_kwargs["middleware"] = cors_middleware

            mcp_server.run(**run_kwargs)

    except KeyboardInterrupt:
        logger.info("Shutdown requested via keyboard interrupt.")
        sys.exit(0)
    except Exception as e:
        logger.error("Server error: %s", e)
        sys.exit(1)