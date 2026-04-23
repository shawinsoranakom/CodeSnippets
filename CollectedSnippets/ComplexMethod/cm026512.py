async def _set_temperature(self, **kwargs) -> None:
        """Set new target temperature."""
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is None:
            return
        try:
            # Get current mode
            mode = self._device.system_mode
            # Set hold if this is not the case
            if self._device.hold_heat is False and self._device.hold_cool is False:
                # Get next period time
                hour_heat, minute_heat = divmod(
                    self._device.raw_ui_data["HeatNextPeriod"] * 15, 60
                )
                hour_cool, minute_cool = divmod(
                    self._device.raw_ui_data["CoolNextPeriod"] * 15, 60
                )
                # Set temporary hold time and temperature
                if mode in COOLING_MODES:
                    await self._device.set_hold_cool(
                        datetime.time(hour_cool, minute_cool), temperature
                    )
                if mode in HEATING_MODES:
                    await self._device.set_hold_heat(
                        datetime.time(hour_heat, minute_heat), temperature
                    )

            # Set temperature if not in auto - set the temperature
            else:
                if mode == "cool":
                    await self._device.set_setpoint_cool(temperature)
                if mode in ["heat", "emheat"]:
                    await self._device.set_setpoint_heat(temperature)

        except (AscConnectionError, UnexpectedResponse) as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="temp_failed",
            ) from err

        except SomeComfortError as err:
            _LOGGER.error("Invalid temperature %.1f: %s", temperature, err)
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="temp_failed_value",
                translation_placeholders={"temperature": temperature},
            ) from err