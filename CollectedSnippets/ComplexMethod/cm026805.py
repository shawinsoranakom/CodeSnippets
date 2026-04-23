def set_heat_cool(self, value: int) -> None:
        """Change operation mode to value if call came from HomeKit."""
        _LOGGER.debug("%s: Set heat-cool to %d", self.entity_id, value)
        params: dict[str, Any] = {ATTR_ENTITY_ID: self.entity_id}
        if value == HC_HEAT_COOL_OFF:
            if self._supports_on_off:
                self.async_call_service(
                    WATER_HEATER_DOMAIN, SERVICE_TURN_OFF, params, "off"
                )
            elif self._off_mode_available and self._supports_operation_mode:
                params[ATTR_OPERATION_MODE] = STATE_OFF
                self.async_call_service(
                    WATER_HEATER_DOMAIN,
                    SERVICE_SET_OPERATION_MODE,
                    params,
                    STATE_OFF,
                )
            else:
                self.char_target_heat_cool.set_value(HC_HEAT_COOL_HEAT)
        elif value == HC_HEAT_COOL_HEAT:
            if self._supports_on_off:
                self.async_call_service(
                    WATER_HEATER_DOMAIN, SERVICE_TURN_ON, params, "on"
                )
            elif self._off_mode_available and self._supports_operation_mode:
                state = self.hass.states.get(self.entity_id)
                if not state:
                    return
                current_operation_mode = state.attributes.get(ATTR_OPERATION_MODE)
                if current_operation_mode and current_operation_mode != STATE_OFF:
                    # Already in a non-off operation mode; do not change it.
                    return
                operation_list = state.attributes.get(ATTR_OPERATION_LIST) or []
                for mode in operation_list:
                    if mode != STATE_OFF:
                        params[ATTR_OPERATION_MODE] = mode
                        self.async_call_service(
                            WATER_HEATER_DOMAIN,
                            SERVICE_SET_OPERATION_MODE,
                            params,
                            mode,
                        )
                        break
        else:
            self.char_target_heat_cool.set_value(HC_HEAT_COOL_HEAT)