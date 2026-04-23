async def async_update(self) -> None:
        """Fetch state from the device."""
        # On state change the device doesn't provide the new state immediately.
        if self._skip_update:
            self._skip_update = False
            return

        try:
            state = await self.hass.async_add_executor_job(self._device.status)
            _LOGGER.debug("Got new state: %s", state)

            self._attr_available = True
            if self._channel_usb:
                self._attr_is_on = state.usb_power
            else:
                self._attr_is_on = state.is_on

            self._attr_extra_state_attributes[ATTR_TEMPERATURE] = state.temperature

            if state.wifi_led:
                self._attr_extra_state_attributes[ATTR_WIFI_LED] = state.wifi_led

            if self._channel_usb is False and state.load_power:
                self._attr_extra_state_attributes[ATTR_LOAD_POWER] = state.load_power

        except DeviceException as ex:
            if self._attr_available:
                self._attr_available = False
                _LOGGER.error("Got exception while fetching the state: %s", ex)