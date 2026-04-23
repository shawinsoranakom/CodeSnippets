def set_state(self, value: bool) -> None:
        """Move switch state to value if call came from HomeKit."""
        _LOGGER.debug("%s: Set switch state to %s", self.entity_id, value)
        if self.activate_only and not value:
            _LOGGER.debug("%s: Ignoring turn_off call", self.entity_id)
            return

        params = {ATTR_ENTITY_ID: self.entity_id}
        if self._domain == "script":
            service = self._object_id
            params = {}
        elif self._domain == button.DOMAIN:
            service = button.SERVICE_PRESS
        elif self._domain == input_button.DOMAIN:
            service = input_button.SERVICE_PRESS
        else:
            service = SERVICE_TURN_ON if value else SERVICE_TURN_OFF

        self.async_call_service(self._domain, service, params)

        if self.activate_only:
            async_call_later(self.hass, ACTIVATE_ONLY_RESET_SECONDS, self.reset_switch)