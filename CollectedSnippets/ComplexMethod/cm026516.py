async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user, reauth or reconfigure."""
        errors: dict[str, str] = {}
        description_placeholders: dict[str, str] = {
            "api_key_url": "https://developers.google.com/maps/documentation/weather/get-api-key",
            "restricting_api_keys_url": "https://developers.google.com/maps/api-security-best-practices#restricting-api-keys",
        }
        if user_input is not None:
            api_key = user_input[CONF_API_KEY]
            referrer = user_input.get(SECTION_API_KEY_OPTIONS, {}).get(CONF_REFERRER)
            self._async_abort_entries_match({CONF_API_KEY: api_key})
            if self.source in (SOURCE_REAUTH, SOURCE_RECONFIGURE):
                entry = (
                    self._get_reauth_entry()
                    if self.source == SOURCE_REAUTH
                    else self._get_reconfigure_entry()
                )
                subentry = next(iter(entry.subentries.values()), None)
                if subentry:
                    latitude = subentry.data[CONF_LATITUDE]
                    longitude = subentry.data[CONF_LONGITUDE]
                else:
                    latitude = self.hass.config.latitude
                    longitude = self.hass.config.longitude
                validation_input = {
                    CONF_LOCATION: {CONF_LATITUDE: latitude, CONF_LONGITUDE: longitude}
                }
            else:
                if _is_location_already_configured(
                    self.hass, user_input[CONF_LOCATION]
                ):
                    return self.async_abort(reason="already_configured")
                validation_input = user_input

            api = GoogleWeatherApi(
                session=async_get_clientsession(self.hass),
                api_key=api_key,
                referrer=referrer,
                language_code=self.hass.config.language,
            )
            if await _validate_input(
                validation_input, api, errors, description_placeholders
            ):
                data = {CONF_API_KEY: api_key, CONF_REFERRER: referrer}
                if self.source in (SOURCE_REAUTH, SOURCE_RECONFIGURE):
                    return self.async_update_reload_and_abort(entry, data=data)

                return self.async_create_entry(
                    title="Google Weather",
                    data=data,
                    subentries=[
                        {
                            "subentry_type": "location",
                            "data": user_input[CONF_LOCATION],
                            "title": user_input[CONF_NAME],
                            "unique_id": None,
                        },
                    ],
                )

        if self.source in (SOURCE_REAUTH, SOURCE_RECONFIGURE):
            entry = (
                self._get_reauth_entry()
                if self.source == SOURCE_REAUTH
                else self._get_reconfigure_entry()
            )
            if user_input is None:
                user_input = {
                    CONF_API_KEY: entry.data.get(CONF_API_KEY),
                    SECTION_API_KEY_OPTIONS: {
                        CONF_REFERRER: entry.data.get(CONF_REFERRER)
                    },
                }
            schema = STEP_USER_DATA_SCHEMA
        else:
            if user_input is None:
                user_input = {}
            schema_dict = STEP_USER_DATA_SCHEMA.schema.copy()
            schema_dict.update(_get_location_schema(self.hass).schema)
            schema = vol.Schema(schema_dict)

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(schema, user_input),
            errors=errors,
            description_placeholders=description_placeholders,
        )