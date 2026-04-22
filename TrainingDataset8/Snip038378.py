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