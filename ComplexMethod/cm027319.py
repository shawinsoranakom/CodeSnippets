def _process_position_valve_update(
        self, msg: ReceiveMessage, position_payload: str, state_payload: str
    ) -> None:
        """Process an update for a valve that reports the position."""
        state: str | None = None
        position_set: bool = False
        if state_payload == self._config[CONF_STATE_OPENING]:
            state = ValveState.OPENING
        elif state_payload == self._config[CONF_STATE_CLOSING]:
            state = ValveState.CLOSING
        elif state_payload == PAYLOAD_NONE:
            self._attr_current_valve_position = None
            return
        if state is None or position_payload != state_payload:
            try:
                percentage_payload = ranged_value_to_percentage(
                    self._range, float(position_payload)
                )
            except ValueError:
                _LOGGER.warning(
                    "Ignoring non numeric payload '%s' received on topic '%s'",
                    position_payload,
                    msg.topic,
                )
            else:
                percentage_payload = min(max(percentage_payload, 0), 100)
                self._attr_current_valve_position = percentage_payload
                # Reset closing and opening if the valve is fully opened or fully closed
                if state is None and percentage_payload in (0, 100):
                    state = RESET_CLOSING_OPENING
                position_set = True
        if state_payload and state is None and not position_set:
            _LOGGER.warning(
                "Payload received on topic '%s' is not one of "
                "[opening, closing], got: %s",
                msg.topic,
                state_payload,
            )
            return
        if state is None:
            return
        self._update_state(state)