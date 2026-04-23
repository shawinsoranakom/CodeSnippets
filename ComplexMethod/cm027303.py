def _update_state(self, msg: ReceiveMessage) -> None:
        # auto-expire enabled?
        if self._expire_after is not None and self._expire_after > 0:
            # When self._expire_after is set, and we receive a message, assume
            # device is not expired since it has to be to receive the message
            self._expired = False

            # Reset old trigger
            if self._expiration_trigger:
                self._expiration_trigger()

            # Set new trigger
            self._expiration_trigger = async_call_later(
                self.hass, self._expire_after, self._value_is_expired
            )

        if template := self._template:
            payload = template(msg.payload, PayloadSentinel.DEFAULT)
        else:
            payload = msg.payload
        if payload is PayloadSentinel.DEFAULT:
            return
        if not isinstance(payload, str):
            _LOGGER.warning(
                "Invalid undecoded state message '%s' received from '%s'",
                payload,
                msg.topic,
            )
            return

        if payload == PAYLOAD_NONE:
            self._attr_native_value = None
            return

        if self._numeric_state_expected:
            if payload == "":
                _LOGGER.debug("Ignore empty state from '%s'", msg.topic)
            else:
                self._attr_native_value = payload
            return

        if self.options and payload not in self.options:
            _LOGGER.warning(
                "Ignoring invalid option received on topic '%s', got '%s', allowed: %s",
                msg.topic,
                payload,
                ", ".join(self.options),
            )
            return

        if self.device_class in {
            None,
            SensorDeviceClass.ENUM,
        } and not check_state_too_long(_LOGGER, payload, self.entity_id, msg):
            self._attr_native_value = payload
            return
        try:
            if (payload_datetime := dt_util.parse_datetime(payload)) is None:
                raise ValueError  # noqa: TRY301
        except ValueError:
            _LOGGER.warning("Invalid state message '%s' from '%s'", payload, msg.topic)
            self._attr_native_value = None
            return
        if self.device_class == SensorDeviceClass.DATE:
            self._attr_native_value = payload_datetime.date()
            return
        self._attr_native_value = payload_datetime