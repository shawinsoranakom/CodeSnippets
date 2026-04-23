def query_attributes(self) -> dict[str, Any]:
        """Return temperature point and modes query attributes."""
        response: dict[str, Any] = {}
        attrs = self.state.attributes
        unit = self.hass.config.units.temperature_unit

        operation = self.state.state
        preset = attrs.get(climate.ATTR_PRESET_MODE)
        supported = attrs.get(ATTR_SUPPORTED_FEATURES, 0)

        if preset in self.preset_to_google:
            response["thermostatMode"] = self.preset_to_google[preset]
        else:
            response["thermostatMode"] = self.hvac_to_google.get(operation, "none")

        current_temp = attrs.get(climate.ATTR_CURRENT_TEMPERATURE)
        if current_temp is not None:
            response["thermostatTemperatureAmbient"] = round(
                TemperatureConverter.convert(
                    current_temp, unit, UnitOfTemperature.CELSIUS
                ),
                1,
            )

        current_humidity = attrs.get(climate.ATTR_CURRENT_HUMIDITY)
        if current_humidity is not None:
            response["thermostatHumidityAmbient"] = current_humidity

        if operation in (climate.HVACMode.AUTO, climate.HVACMode.HEAT_COOL):
            if supported & ClimateEntityFeature.TARGET_TEMPERATURE_RANGE:
                response["thermostatTemperatureSetpointHigh"] = round(
                    TemperatureConverter.convert(
                        attrs[climate.ATTR_TARGET_TEMP_HIGH],
                        unit,
                        UnitOfTemperature.CELSIUS,
                    ),
                    1,
                )
                response["thermostatTemperatureSetpointLow"] = round(
                    TemperatureConverter.convert(
                        attrs[climate.ATTR_TARGET_TEMP_LOW],
                        unit,
                        UnitOfTemperature.CELSIUS,
                    ),
                    1,
                )
            elif (target_temp := attrs.get(ATTR_TEMPERATURE)) is not None:
                target_temp = round(
                    TemperatureConverter.convert(
                        target_temp, unit, UnitOfTemperature.CELSIUS
                    ),
                    1,
                )
                response["thermostatTemperatureSetpointHigh"] = target_temp
                response["thermostatTemperatureSetpointLow"] = target_temp
        elif (target_temp := attrs.get(ATTR_TEMPERATURE)) is not None:
            response["thermostatTemperatureSetpoint"] = round(
                TemperatureConverter.convert(
                    target_temp, unit, UnitOfTemperature.CELSIUS
                ),
                1,
            )

        return response