async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle re-configuration with Trafikverket."""
        errors: dict[str, str] = {}

        if user_input:
            try:
                await self.validate_input(
                    user_input[CONF_API_KEY], user_input[CONF_STATION]
                )
            except InvalidAuthentication:
                errors["base"] = "invalid_auth"
            except NoWeatherStationFound:
                errors["base"] = "invalid_station"
            except MultipleWeatherStationsFound:
                errors["base"] = "more_stations"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "cannot_connect"
            else:
                return self.async_update_reload_and_abort(
                    self._get_reconfigure_entry(),
                    title=user_input[CONF_STATION],
                    data=user_input,
                )

        schema = self.add_suggested_values_to_schema(
            vol.Schema(
                {
                    vol.Required(CONF_API_KEY): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.PASSWORD)
                    ),
                    vol.Required(CONF_STATION): TextSelector(),
                }
            ),
            {**self._get_reconfigure_entry().data, **(user_input or {})},
        )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=schema,
            errors=errors,
        )