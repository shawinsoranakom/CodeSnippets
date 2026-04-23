async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the user-based step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self._async_abort_entries_match(user_input)
            host = user_input[CONF_HOST]
            session = async_get_clientsession(self.hass)
            hub = WebControlPro(host, session)
            try:
                pong = await hub.ping()
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                if not pong:
                    errors["base"] = "cannot_connect"
                else:
                    await hub.refresh()
                    rooms = set(hub.rooms.keys())
                    for entry in self.hass.config_entries.async_loaded_entries(DOMAIN):
                        if (
                            entry.runtime_data
                            and entry.runtime_data.rooms
                            and set(entry.runtime_data.rooms.keys()) == rooms
                        ):
                            return self.async_abort(reason="already_configured")
                    return self.async_create_entry(title=host, data=user_input)

        if self.source == SOURCE_DHCP:
            discovery_info: DhcpServiceInfo = self.init_data
            data_values = {CONF_HOST: discovery_info.ip}
        else:
            data_values = {CONF_HOST: SUGGESTED_HOST}

        self.context["title_placeholders"] = data_values
        data_schema = self.add_suggested_values_to_schema(
            STEP_USER_DATA_SCHEMA, data_values
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )