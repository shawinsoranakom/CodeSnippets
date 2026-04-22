def run(
    main_script_path: str,
    command_line: Optional[str],
    args: List[str],
    flag_options: Dict[str, Any],
) -> None:
    """Run a script in a separate thread and start a server for the app.

    This starts a blocking asyncio eventloop.
    """
    _fix_sys_path(main_script_path)
    _fix_matplotlib_crash()
    _fix_tornado_crash()
    _fix_sys_argv(main_script_path, args)
    _fix_pydeck_mapbox_api_warning()
    _install_config_watchers(flag_options)
    _install_pages_watcher(main_script_path)

    # Create the server. It won't start running yet.
    server = Server(main_script_path, command_line)

    async def run_server() -> None:
        # Start the server
        await server.start()
        _on_server_start(server)

        # Install a signal handler that will shut down the server
        # and close all our threads
        _set_up_signal_handler(server)

        # Wait until `Server.stop` is called, either by our signal handler, or
        # by a debug websocket session.
        await server.stopped

    # Run the server. This function will not return until the server is shut down.
    asyncio.run(run_server())