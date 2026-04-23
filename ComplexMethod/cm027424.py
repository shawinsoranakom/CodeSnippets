async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            api_key = user_input.get(CONF_API_KEY)
            self._async_abort_entries_match({CONF_API_KEY: api_key})
            if api_key:
                # Test the API key by trying to fetch bus data
                session = async_get_clientsession(self.hass)
                bus_feed = BusFeed(api_key=api_key, session=session)
                try:
                    # Try to get stops for a known route to validate the key
                    await bus_feed.get_stops(route_id="M15")
                except MTAFeedError:
                    errors["base"] = "cannot_connect"
                except Exception:
                    _LOGGER.exception("Unexpected error validating API key")
                    errors["base"] = "unknown"
            if not errors:
                if self.source == SOURCE_REAUTH:
                    return self.async_update_reload_and_abort(
                        self._get_reauth_entry(),
                        data_updates={CONF_API_KEY: api_key or None},
                    )
                return self.async_create_entry(
                    title="MTA",
                    data={CONF_API_KEY: api_key or None},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_API_KEY): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.PASSWORD)
                    ),
                }
            ),
            errors=errors,
        )