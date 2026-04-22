async def start(self) -> None:
        """Start the server.

        When this returns, Streamlit is ready to accept new sessions.
        """

        LOGGER.debug("Starting server...")

        app = self._create_app()
        start_listening(app)

        port = config.get_option("server.port")
        LOGGER.debug("Server started on port %s", port)

        await self._runtime.start()