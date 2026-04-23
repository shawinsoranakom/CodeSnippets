async def execute(self, command, data, params, challenge):
        """Execute a temperature point or mode command."""
        # All sent in temperatures are always in Celsius
        unit = self.hass.config.units.temperature_unit
        min_temp = self.state.attributes[climate.ATTR_MIN_TEMP]
        max_temp = self.state.attributes[climate.ATTR_MAX_TEMP]

        if command == COMMAND_THERMOSTAT_TEMPERATURE_SETPOINT:
            temp = TemperatureConverter.convert(
                params["thermostatTemperatureSetpoint"], UnitOfTemperature.CELSIUS, unit
            )
            if unit == UnitOfTemperature.FAHRENHEIT:
                temp = round(temp)

            if temp < min_temp or temp > max_temp:
                raise SmartHomeError(
                    ERR_VALUE_OUT_OF_RANGE,
                    f"Temperature should be between {min_temp} and {max_temp}",
                )

            await self.hass.services.async_call(
                climate.DOMAIN,
                climate.SERVICE_SET_TEMPERATURE,
                {ATTR_ENTITY_ID: self.state.entity_id, ATTR_TEMPERATURE: temp},
                blocking=not self.config.should_report_state,
                context=data.context,
            )

        elif command == COMMAND_THERMOSTAT_TEMPERATURE_SET_RANGE:
            temp_high = TemperatureConverter.convert(
                params["thermostatTemperatureSetpointHigh"],
                UnitOfTemperature.CELSIUS,
                unit,
            )
            if unit == UnitOfTemperature.FAHRENHEIT:
                temp_high = round(temp_high)

            if temp_high < min_temp or temp_high > max_temp:
                raise SmartHomeError(
                    ERR_VALUE_OUT_OF_RANGE,
                    (
                        "Upper bound for temperature range should be between "
                        f"{min_temp} and {max_temp}"
                    ),
                )

            temp_low = TemperatureConverter.convert(
                params["thermostatTemperatureSetpointLow"],
                UnitOfTemperature.CELSIUS,
                unit,
            )
            if unit == UnitOfTemperature.FAHRENHEIT:
                temp_low = round(temp_low)

            if temp_low < min_temp or temp_low > max_temp:
                raise SmartHomeError(
                    ERR_VALUE_OUT_OF_RANGE,
                    (
                        "Lower bound for temperature range should be between "
                        f"{min_temp} and {max_temp}"
                    ),
                )

            supported = self.state.attributes.get(ATTR_SUPPORTED_FEATURES)
            svc_data = {ATTR_ENTITY_ID: self.state.entity_id}

            if supported & ClimateEntityFeature.TARGET_TEMPERATURE_RANGE:
                svc_data[climate.ATTR_TARGET_TEMP_HIGH] = temp_high
                svc_data[climate.ATTR_TARGET_TEMP_LOW] = temp_low
            else:
                svc_data[ATTR_TEMPERATURE] = (temp_high + temp_low) / 2

            await self.hass.services.async_call(
                climate.DOMAIN,
                climate.SERVICE_SET_TEMPERATURE,
                svc_data,
                blocking=not self.config.should_report_state,
                context=data.context,
            )

        elif command == COMMAND_THERMOSTAT_SET_MODE:
            target_mode = params["thermostatMode"]
            supported = self.state.attributes.get(ATTR_SUPPORTED_FEATURES)

            if target_mode == "on":
                await self.hass.services.async_call(
                    climate.DOMAIN,
                    SERVICE_TURN_ON,
                    {ATTR_ENTITY_ID: self.state.entity_id},
                    blocking=not self.config.should_report_state,
                    context=data.context,
                )
                return

            if target_mode == "off":
                await self.hass.services.async_call(
                    climate.DOMAIN,
                    SERVICE_TURN_OFF,
                    {ATTR_ENTITY_ID: self.state.entity_id},
                    blocking=not self.config.should_report_state,
                    context=data.context,
                )
                return

            if target_mode in self.google_to_preset:
                await self.hass.services.async_call(
                    climate.DOMAIN,
                    climate.SERVICE_SET_PRESET_MODE,
                    {
                        climate.ATTR_PRESET_MODE: self.google_to_preset[target_mode],
                        ATTR_ENTITY_ID: self.state.entity_id,
                    },
                    blocking=not self.config.should_report_state,
                    context=data.context,
                )
                return

            await self.hass.services.async_call(
                climate.DOMAIN,
                climate.SERVICE_SET_HVAC_MODE,
                {
                    ATTR_ENTITY_ID: self.state.entity_id,
                    climate.ATTR_HVAC_MODE: self.google_to_hvac[target_mode],
                },
                blocking=not self.config.should_report_state,
                context=data.context,
            )