async def _async_websocket_command_phase(
        self, connection: ActiveConnection
    ) -> None:
        """Handle the command phase of the websocket connection."""
        wsock = self._wsock
        async_handle_str = connection.async_handle
        async_handle_binary = connection.async_handle_binary

        # Command phase
        while not wsock.closed:
            msg = await wsock.receive()
            msg_type = msg.type
            msg_data = msg.data

            if msg_type in CLOSE_MSG_TYPES:
                break

            if msg_type is WSMsgType.BINARY:
                if len(msg_data) < 1:
                    raise Disconnect("Received invalid binary message.")

                handler = msg_data[0]
                payload = msg_data[1:]
                async_handle_binary(handler, payload)
                continue

            if msg_type is not WSMsgType.TEXT:
                if msg_type is WSMsgType.ERROR:
                    # msg.data is the exception
                    raise Disconnect(
                        f"Received error message during command phase: {msg.data}"
                    )
                raise Disconnect(f"Received non-Text message of type {msg_type}.")

            try:
                command_msg_data = json_loads(msg_data)
            except ValueError as ex:
                raise Disconnect("Received invalid JSON.") from ex

            if self._debug:
                self._logger.debug(
                    "%s: Received %s", self.description, command_msg_data
                )

            # command_msg_data is always deserialized from JSON as a list
            if type(command_msg_data) is not list:
                async_handle_str(command_msg_data)
                continue

            for split_msg in command_msg_data:
                async_handle_str(split_msg)