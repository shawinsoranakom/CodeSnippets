def _state_message_received(self, msg: ReceiveMessage) -> None:
        """Handle a new received MQTT state message."""

        # auto-expire enabled?
        if self._expire_after:
            # When expire_after is set, and we receive a message, assume device is
            # not expired since it has to be to receive the message
            self._expired = False

            # Reset old trigger
            if self._expiration_trigger:
                self._expiration_trigger()

            # Set new trigger
            self._expiration_trigger = async_call_later(
                self.hass, self._expire_after, self._value_is_expired
            )

        payload = self._value_template(msg.payload)
        if not payload.strip():  # No output from template, ignore
            _LOGGER.debug(
                (
                    "Empty template output for entity: %s with state topic: %s."
                    " Payload: '%s', with value template '%s'"
                ),
                self.entity_id,
                self._config[CONF_STATE_TOPIC],
                msg.payload,
                self._config.get(CONF_VALUE_TEMPLATE),
            )
            return

        if payload == self._config[CONF_PAYLOAD_ON]:
            self._attr_is_on = True
        elif payload == self._config[CONF_PAYLOAD_OFF]:
            self._attr_is_on = False
        elif payload == PAYLOAD_NONE:
            self._attr_is_on = None
        else:  # Payload is not for this entity
            template_info = ""
            if self._config.get(CONF_VALUE_TEMPLATE) is not None:
                template_info = (
                    f", template output: '{payload!s}', with value template"
                    f" '{self._config.get(CONF_VALUE_TEMPLATE)!s}'"
                )
            _LOGGER.info(
                (
                    "No matching payload found for entity: %s with state topic: %s."
                    " Payload: '%s'%s"
                ),
                self.entity_id,
                self._config[CONF_STATE_TOPIC],
                msg.payload,
                template_info,
            )
            return

        if self._delay_listener is not None:
            self._delay_listener()
            self._delay_listener = None

        off_delay: int | None = self._config.get(CONF_OFF_DELAY)
        if self._attr_is_on and off_delay is not None:
            self._delay_listener = evt.async_call_later(
                self.hass, off_delay, self._off_delay_listener
            )