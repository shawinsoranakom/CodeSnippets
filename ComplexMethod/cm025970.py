def message_received(msg):
            """Handle new MQTT messages."""
            try:
                data = MQTT_PAYLOAD(msg.payload)
            except vol.MultipleInvalid as error:
                _LOGGER.debug("Skipping update because of malformatted data: %s", error)
                return

            device = _parse_update_data(msg.topic, data)
            if device.get(CONF_DEVICE_ID) == self._device_id:
                if self._distance is None or self._updated is None:
                    update_state(**device)
                else:
                    # update if:
                    # device is in the same room OR
                    # device is closer to another room OR
                    # last update from other room was too long ago
                    timediff = dt_util.utcnow() - self._updated
                    if (
                        device.get(ATTR_ROOM) == self._state
                        or device.get(ATTR_DISTANCE) < self._distance
                        or timediff.total_seconds() >= self._timeout
                    ):
                        update_state(**device)