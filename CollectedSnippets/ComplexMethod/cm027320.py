def _state_message_received(self, msg: ReceiveMessage) -> None:
        """Handle new MQTT state messages."""
        payload = self._value_template(msg.payload)
        payload_dict: Any = None
        position_payload: Any = payload
        state_payload: Any = payload

        if not payload:
            _LOGGER.debug("Ignoring empty state message from '%s'", msg.topic)
            return

        with suppress(*JSON_DECODE_EXCEPTIONS):
            payload_dict = json_loads(payload)
            if isinstance(payload_dict, dict):
                if self.reports_position and "position" not in payload_dict:
                    _LOGGER.warning(
                        "Missing required `position` attribute in json payload "
                        "on topic '%s', got: %s",
                        msg.topic,
                        payload,
                    )
                    return
                if not self.reports_position and "state" not in payload_dict:
                    _LOGGER.warning(
                        "Missing required `state` attribute in json payload "
                        " on topic '%s', got: %s",
                        msg.topic,
                        payload,
                    )
                    return
                position_payload = payload_dict.get("position")
                state_payload = payload_dict.get("state")

        if self._config[CONF_REPORTS_POSITION]:
            self._process_position_valve_update(msg, position_payload, state_payload)
        else:
            self._process_binary_valve_update(msg, state_payload)