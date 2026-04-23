async def async_step_api_key(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the API key step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api = _create_volvo_cars_api(
                self.hass,
                self._config_data[CONF_TOKEN][CONF_ACCESS_TOKEN],
                user_input[CONF_API_KEY],
            )

            # Try to load all vehicles on the account. If it succeeds
            # it means that the given API key is correct. The vehicle info
            # is used in the VIN step.
            try:
                await self._async_load_vehicles(api)
            except VolvoApiException:
                _LOGGER.exception("Unable to retrieve vehicles")
                errors["base"] = "cannot_load_vehicles"

            if not errors:
                self._config_data |= user_input
                return await self.async_step_vin()

        if user_input is None:
            if self.source == SOURCE_REAUTH:
                user_input = self._config_data
                api = _create_volvo_cars_api(
                    self.hass,
                    self._config_data[CONF_TOKEN][CONF_ACCESS_TOKEN],
                    self._config_data[CONF_API_KEY],
                )

                # Test if the configured API key is still valid. If not, show this
                # form. If it is, skip this step and go directly to the next step.
                try:
                    await self._async_load_vehicles(api)
                    return await self.async_step_vin()
                except VolvoApiException:
                    pass

            elif self.source == SOURCE_RECONFIGURE:
                user_input = self._config_data = dict(
                    self._get_reconfigure_entry().data
                )
            else:
                user_input = {}

        schema = self.add_suggested_values_to_schema(
            vol.Schema(
                {
                    vol.Required(CONF_API_KEY): TextSelector(
                        TextSelectorConfig(
                            type=TextSelectorType.TEXT, autocomplete="password"
                        )
                    ),
                }
            ),
            {
                CONF_API_KEY: user_input.get(CONF_API_KEY, ""),
            },
        )

        return self.async_show_form(
            step_id="api_key",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "volvo_dev_portal": "https://developer.volvocars.com/account/#your-api-applications"
            },
        )