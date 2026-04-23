def _state_message_received(self, msg: ReceiveMessage) -> None:
        """Handle new MQTT state messages."""
        payload = self._value_template(msg.payload)
        if not payload or payload == PAYLOAD_EMPTY_JSON:
            _LOGGER.debug(
                "Ignoring empty payload '%s' after rendering for topic %s",
                payload,
                msg.topic,
            )
            return
        json_payload: dict[str, Any] = {}
        if payload in [self._state_on, self._state_off, PAYLOAD_NONE]:
            json_payload = {STATE: payload}
        else:
            try:
                json_payload = json_loads_object(payload)
                _LOGGER.debug(
                    "JSON payload detected after processing payload '%s' on topic %s",
                    json_payload,
                    msg.topic,
                )
            except JSON_DECODE_EXCEPTIONS:
                _LOGGER.warning(
                    (
                        "No valid (JSON) payload detected after processing payload"
                        " '%s' on topic %s"
                    ),
                    json_payload,
                    msg.topic,
                )
                return
        if STATE in json_payload:
            if json_payload[STATE] == self._state_on:
                self._attr_is_on = True
            if json_payload[STATE] == self._state_off:
                self._attr_is_on = False
            if json_payload[STATE] == PAYLOAD_NONE:
                self._attr_is_on = None
            del json_payload[STATE]

        if json_payload:
            # process attributes
            try:
                params: SirenTurnOnServiceParameters
                params = vol.All(TURN_ON_SCHEMA)(json_payload)
            except vol.MultipleInvalid as invalid_siren_parameters:
                _LOGGER.warning(
                    "Unable to update siren state attributes from payload '%s': %s",
                    json_payload,
                    invalid_siren_parameters,
                )
                return
            # To be able to track changes to self._extra_attributes we assign
            # a fresh copy to make the original tracked reference immutable.
            self._extra_attributes = dict(self._extra_attributes)
            self._update(process_turn_on_params(self, params))