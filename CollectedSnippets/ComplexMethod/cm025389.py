def handle_ws_update(self, new_state: dict[str, Any]) -> None:
        """Update entity state from WebSocket callback."""
        available = process_connection_update(new_state)
        if available is not None:
            self._attr_available = available
            if not available:
                if not self._unavailable_logged:
                    _LOGGER.info("The entity %s is unavailable", self.entity_id)
                    self._unavailable_logged = True
            elif self._unavailable_logged:
                _LOGGER.info("The entity %s is back online", self.entity_id)
                self._unavailable_logged = False

        if not new_state:
            return

        if "currentTemp" in new_state:
            self._attr_current_temperature = new_state["currentTemp"]
        if "overrideTemp" in new_state:
            self._attr_target_temperature = new_state["overrideTemp"]
        elif "targetTemp" in new_state:
            self._attr_target_temperature = new_state["targetTemp"]
        if "targetMode" in new_state:
            self._attr_preset_mode = REVERSE_PRESET_MODE_MAP.get(
                new_state["targetMode"]
            )
            if self._attr_preset_mode and self._attr_preset_mode != "standby":
                self._last_preset_mode = self._attr_preset_mode
            if self._attr_preset_mode == "standby":
                self._attr_hvac_mode = HVACMode.OFF
            elif self._attr_hvac_mode == HVACMode.OFF:
                self._attr_hvac_mode = next(
                    (
                        mode
                        for mode in self._attr_hvac_modes
                        if mode is not HVACMode.OFF
                    ),
                    HVACMode.HEAT,
                )
        if "changeOverUser" in new_state and self._device.get("model") == "NTD":
            if new_state["changeOverUser"] == 1:
                self._attr_hvac_modes = [HVACMode.COOL, HVACMode.OFF]

                if (
                    self._attr_hvac_mode != HVACMode.OFF
                    and self._attr_preset_mode != "standby"
                ):
                    self._attr_hvac_mode = HVACMode.COOL
            else:
                self._attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]

                if (
                    self._attr_hvac_mode != HVACMode.OFF
                    and self._attr_preset_mode != "standby"
                ):
                    self._attr_hvac_mode = HVACMode.HEAT
        self.async_write_ha_state()