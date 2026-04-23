def _attributes_message_received(self, msg: ReceiveMessage) -> None:
        """Update extra state attributes."""
        payload = (
            self._attr_tpl(msg.payload) if self._attr_tpl is not None else msg.payload
        )
        try:
            json_dict = json_loads(payload) if isinstance(payload, str) else None
        except ValueError:
            _LOGGER.warning("Erroneous JSON: %s", payload)
        else:
            if isinstance(json_dict, dict):
                filtered_dict: dict[str, Any] = {
                    k: v
                    for k, v in json_dict.items()
                    if k not in MQTT_ATTRIBUTES_BLOCKED
                    and k not in self._attributes_extra_blocked
                }
                if hasattr(self, "_process_update_extra_state_attributes"):
                    self._process_update_extra_state_attributes(filtered_dict)
                else:
                    self._attr_extra_state_attributes = filtered_dict

            else:
                _LOGGER.warning("JSON result was not a dictionary")