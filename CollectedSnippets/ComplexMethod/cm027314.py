def _position_message_received(self, msg: ReceiveMessage) -> None:
        """Handle new MQTT position messages."""
        payload: ReceivePayloadType = self._get_position_template(msg.payload)
        payload_dict: Any = None

        if not payload:
            _LOGGER.debug("Ignoring empty position message from '%s'", msg.topic)
            return

        with suppress(*JSON_DECODE_EXCEPTIONS):
            payload_dict = json_loads(payload)

        if payload_dict and isinstance(payload_dict, dict):
            if "position" not in payload_dict:
                _LOGGER.warning(
                    "Template (position_template) returned JSON without position"
                    " attribute"
                )
                return
            if "tilt_position" in payload_dict:
                if not self._config.get(CONF_TILT_STATE_OPTIMISTIC):
                    # reset forced set tilt optimistic
                    self._tilt_optimistic = False
                self.tilt_payload_received(payload_dict["tilt_position"])
            payload = payload_dict["position"]

        try:
            percentage_payload = ranged_value_to_percentage(
                self._pos_range, float(payload)
            )
        except ValueError:
            _LOGGER.warning("Payload '%s' is not numeric", payload)
            return

        self._attr_current_cover_position = min(100, max(0, percentage_payload))
        if self._config.get(CONF_STATE_TOPIC) is None:
            self._update_state(
                CoverState.CLOSED
                if self.current_cover_position == 0
                else CoverState.OPEN
            )