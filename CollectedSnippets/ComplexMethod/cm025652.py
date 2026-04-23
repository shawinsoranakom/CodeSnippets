async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        errors = {}
        use_nearest = False

        websession = async_get_clientsession(self.hass)

        if user_input is not None:
            await self.async_set_unique_id(
                f"{user_input[CONF_LATITUDE]}-{user_input[CONF_LONGITUDE]}"
            )
            self._abort_if_unique_id_configured()
            try:
                location_point_valid = await check_location(
                    websession,
                    user_input["api_key"],
                    user_input["latitude"],
                    user_input["longitude"],
                )
                if not location_point_valid:
                    location_nearest_valid = await check_location(
                        websession,
                        user_input["api_key"],
                        user_input["latitude"],
                        user_input["longitude"],
                        use_nearest=True,
                    )
            except AirlyError as err:
                if err.status_code == HTTPStatus.UNAUTHORIZED:
                    errors["base"] = "invalid_api_key"
                if err.status_code == HTTPStatus.NOT_FOUND:
                    errors["base"] = "wrong_location"
            else:
                if not location_point_valid:
                    if not location_nearest_valid:
                        return self.async_abort(reason="wrong_location")
                    use_nearest = True
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data={**user_input, CONF_USE_NEAREST: use_nearest},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY): str,
                    vol.Optional(
                        CONF_LATITUDE, default=self.hass.config.latitude
                    ): cv.latitude,
                    vol.Optional(
                        CONF_LONGITUDE, default=self.hass.config.longitude
                    ): cv.longitude,
                    vol.Optional(
                        CONF_NAME, default=self.hass.config.location_name
                    ): str,
                }
            ),
            errors=errors,
            description_placeholders=DESCRIPTION_PLACEHOLDERS,
        )