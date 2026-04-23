def on_message(self, payload: Union[str, bytes]) -> None:
        if not self._session_id:
            return

        try:
            if isinstance(payload, str):
                # Sanity check. (The frontend should only be sending us bytes;
                # Protobuf.ParseFromString does not accept str input.)
                raise RuntimeError(
                    "WebSocket received an unexpected `str` message. "
                    "(We expect `bytes` only.)"
                )

            msg = BackMsg()
            msg.ParseFromString(payload)
            _LOGGER.debug("Received the following back message:\n%s", msg)

        except Exception as ex:
            _LOGGER.error(ex)
            self._runtime.handle_backmsg_deserialization_exception(self._session_id, ex)
            return

        if msg.WhichOneof("type") == "close_connection":
            # "close_connection" is a special developmentMode-only
            # message used in e2e tests to test disabling widgets.
            if config.get_option("global.developmentMode"):
                self._runtime.stop()
            else:
                _LOGGER.warning(
                    "Client tried to close connection when " "not in development mode"
                )
        else:
            # AppSession handles all other BackMsg types.
            self._runtime.handle_backmsg(self._session_id, msg)