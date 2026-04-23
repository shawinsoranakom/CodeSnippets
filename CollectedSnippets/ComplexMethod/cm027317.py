def _message_received(self, msg: ReceiveMessage) -> None:
        """Handle new MQTT messages."""
        num_value: int | float | None
        payload = str(self._value_template(msg.payload))
        if not payload.strip():
            _LOGGER.debug("Ignoring empty state update from '%s'", msg.topic)
            return
        try:
            if payload == self._config[CONF_PAYLOAD_RESET]:
                num_value = None
            elif payload.isnumeric():
                num_value = int(payload)
            else:
                num_value = float(payload)
        except ValueError:
            _LOGGER.warning("Payload '%s' is not a Number", msg.payload)
            return

        if num_value is not None and (
            num_value < self.native_min_value or num_value > self.native_max_value
        ):
            _LOGGER.error(
                "Invalid value for %s: %s (range %s - %s)",
                self.entity_id,
                num_value,
                self.native_min_value,
                self.native_max_value,
            )
            return

        self._attr_native_value = num_value