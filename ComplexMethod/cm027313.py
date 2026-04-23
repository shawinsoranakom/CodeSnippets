def _state_message_received(self, msg: ReceiveMessage) -> None:
        """Handle new MQTT state messages."""
        payload = self._value_template(msg.payload)

        if not payload:
            _LOGGER.debug("Ignoring empty state message from '%s'", msg.topic)
            return

        state: str | None
        if payload == self._config[CONF_STATE_STOPPED]:
            if self._config.get(CONF_GET_POSITION_TOPIC) is not None:
                state = (
                    CoverState.CLOSED
                    if self._attr_current_cover_position == DEFAULT_POSITION_CLOSED
                    else CoverState.OPEN
                )
            else:
                state = (
                    CoverState.CLOSED
                    if self.state in [CoverState.CLOSED, CoverState.CLOSING]
                    else CoverState.OPEN
                )
        elif payload == self._config[CONF_STATE_OPENING]:
            state = CoverState.OPENING
        elif payload == self._config[CONF_STATE_CLOSING]:
            state = CoverState.CLOSING
        elif payload == self._config[CONF_STATE_OPEN]:
            state = CoverState.OPEN
        elif payload == self._config[CONF_STATE_CLOSED]:
            state = CoverState.CLOSED
        elif payload == PAYLOAD_NONE:
            state = None
        else:
            _LOGGER.warning(
                (
                    "Payload is not supported (e.g. open, closed, opening, closing,"
                    " stopped): %s"
                ),
                payload,
            )
            return
        self._update_state(state)