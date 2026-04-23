def get_property(self, name: str) -> Any:
        """Read and return a property."""
        if self.entity.state == STATE_UNAVAILABLE:
            return None

        if name == "thermostatMode":
            if self.entity.domain == water_heater.DOMAIN:
                return None
            preset = self.entity.attributes.get(climate.ATTR_PRESET_MODE)

            mode: dict[str, str] | str | None
            if preset in API_THERMOSTAT_PRESETS:
                mode = API_THERMOSTAT_PRESETS[preset]
            elif self.entity.state == STATE_UNKNOWN:
                return None
            else:
                if self.entity.state not in API_THERMOSTAT_MODES:
                    _LOGGER.error(
                        "%s (%s) has unsupported state value '%s'",
                        self.entity.entity_id,
                        type(self.entity),
                        self.entity.state,
                    )
                    raise UnsupportedProperty(name)
                mode = API_THERMOSTAT_MODES[HVACMode(self.entity.state)]
            return mode

        unit = self.hass.config.units.temperature_unit
        if name == "targetSetpoint":
            temp = self.entity.attributes.get(ATTR_TEMPERATURE)
        elif name == "lowerSetpoint":
            temp = self.entity.attributes.get(climate.ATTR_TARGET_TEMP_LOW)
        elif name == "upperSetpoint":
            temp = self.entity.attributes.get(climate.ATTR_TARGET_TEMP_HIGH)
        else:
            raise UnsupportedProperty(name)

        if temp is None:
            return None

        try:
            temp = float(temp)
        except ValueError:
            _LOGGER.warning(
                "Invalid temp value %s for %s in %s", temp, name, self.entity.entity_id
            )
            return None

        return {"value": temp, "scale": API_TEMP_UNITS[unit]}