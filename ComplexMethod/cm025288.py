async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            await self.async_set_unique_id(
                unique_id=_get_unique_id(self.hass, user_input)
            )
            self._abort_if_unique_id_configured()

            location = user_input[CONF_LOCATION]
            latitude = location[CONF_LATITUDE]
            longitude = location[CONF_LONGITUDE]
            if CONF_NAME not in user_input:
                user_input[CONF_NAME] = DEFAULT_NAME
                # Append zone name if it exists and we are using the default name
                if zone_state := async_active_zone(self.hass, latitude, longitude):
                    zone_name = zone_state.attributes[CONF_FRIENDLY_NAME]
                    user_input[CONF_NAME] += f" - {zone_name}"
            try:
                await TomorrowioV4(
                    user_input[CONF_API_KEY],
                    str(latitude),
                    str(longitude),
                    session=async_get_clientsession(self.hass),
                ).realtime([TMRW_ATTR_TEMPERATURE])
            except CantConnectException:
                errors["base"] = "cannot_connect"
            except InvalidAPIKeyException:
                errors[CONF_API_KEY] = "invalid_api_key"
            except RateLimitedException:
                errors[CONF_API_KEY] = "rate_limited"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

            if not errors:
                options: Mapping[str, Any] = {CONF_TIMESTEP: DEFAULT_TIMESTEP}
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data=user_input,
                    options=options,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_get_config_schema(self.hass, self.source, user_input),
            errors=errors,
            description_placeholders={
                "signup_link": "[Tomorrow.io](https://app.tomorrow.io/signup)"
            },
        )