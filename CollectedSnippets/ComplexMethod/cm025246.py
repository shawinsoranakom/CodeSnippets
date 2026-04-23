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
            self._attr_is_on = state.is_on
            self._attr_extra_state_attributes.update(
                {ATTR_TEMPERATURE: state.temperature, ATTR_LOAD_POWER: state.load_power}
            )

            if self._device_features & FEATURE_SET_POWER_MODE == 1 and state.mode:
                self._attr_extra_state_attributes[ATTR_POWER_MODE] = state.mode.value

            if self._device_features & FEATURE_SET_WIFI_LED == 1 and state.wifi_led:
                self._attr_extra_state_attributes[ATTR_WIFI_LED] = state.wifi_led

            if (
                self._device_features & FEATURE_SET_POWER_PRICE == 1
                and state.power_price
            ):
                self._attr_extra_state_attributes[ATTR_POWER_PRICE] = state.power_price

        except DeviceException as ex:
            if self._attr_available:
                self._attr_available = False
                _LOGGER.error("Got exception while fetching the state: %s", ex)