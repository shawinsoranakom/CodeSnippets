async def _async_handle_auth_phase(
        self,
        auth: AuthPhase,
        send_bytes_text: Callable[[bytes], Coroutine[Any, Any, None]],
    ) -> ActiveConnection:
        """Handle the auth phase of the websocket connection."""
        request = self._request

        if is_supervisor_unix_socket_request(request):
            # Unix socket requests are pre-authenticated by the HTTP
            # auth middleware — skip the token exchange.
            connection = await auth.async_handle_supervisor_unix_socket()
        else:
            await send_bytes_text(AUTH_REQUIRED_MESSAGE)

            # Auth Phase
            try:
                msg = await self._wsock.receive(AUTH_MESSAGE_TIMEOUT)
            except TimeoutError as err:
                raise Disconnect(
                    f"Did not receive auth message within {AUTH_MESSAGE_TIMEOUT} seconds"
                ) from err

            if msg.type in (WSMsgType.CLOSE, WSMsgType.CLOSED, WSMsgType.CLOSING):
                raise Disconnect("Received close message during auth phase")

            if msg.type is not WSMsgType.TEXT:
                if msg.type is WSMsgType.ERROR:
                    # msg.data is the exception
                    raise Disconnect(
                        f"Received error message during auth phase: {msg.data}"
                    )
                raise Disconnect(
                    f"Received non-Text message of type {msg.type} during auth phase"
                )

            try:
                auth_msg_data = json_loads(msg.data)
            except ValueError as err:
                raise Disconnect("Received invalid JSON during auth phase") from err

            if self._debug:
                self._logger.debug("%s: Received %s", self.description, auth_msg_data)
            connection = await auth.async_handle(auth_msg_data)

        # As the webserver is now started before the start
        # event we do not want to block for websocket responses
        #
        # We only start the writer queue after the auth phase is completed
        # since there is no need to queue messages before the auth phase
        self._connection = connection
        self._writer_task = create_eager_task(self._writer(connection, send_bytes_text))
        self._hass.data[DATA_CONNECTIONS] = self._hass.data.get(DATA_CONNECTIONS, 0) + 1
        async_dispatcher_send(self._hass, SIGNAL_WEBSOCKET_CONNECTED)

        self._authenticated = True
        return connection