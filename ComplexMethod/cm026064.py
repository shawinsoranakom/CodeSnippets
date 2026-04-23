async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Dialog that informs the user that reauth is required."""
        errors: dict[str, str] = {}
        placeholders: dict[str, str] = {}
        reauth_entry = self._get_reauth_entry()
        entry_data = reauth_entry.data
        host = entry_data[CONF_HOST]
        port = entry_data.get(CONF_PORT)

        if user_input:
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]
            credentials = Credentials(username, password)
            try:
                device = await self._async_try_discover_and_update(
                    host,
                    credentials=credentials,
                    raise_on_progress=False,
                    raise_on_timeout=False,
                    port=port,
                ) or await self._async_try_connect_all(
                    host,
                    credentials=credentials,
                    raise_on_progress=False,
                    port=port,
                )
            except AuthenticationError as ex:
                errors[CONF_PASSWORD] = "invalid_auth"
                placeholders["error"] = str(ex)
            except KasaException as ex:
                errors["base"] = "cannot_connect"
                placeholders["error"] = str(ex)
            else:
                if not device:
                    errors["base"] = "cannot_connect"
                    placeholders["error"] = "try_connect_all failed"
                else:
                    await self.async_set_unique_id(
                        dr.format_mac(device.mac),
                        raise_on_progress=False,
                    )
                    await set_credentials(self.hass, username, password)
                    if updates := self._get_config_updates(reauth_entry, host, device):
                        self.hass.config_entries.async_update_entry(
                            reauth_entry, data=updates
                        )
                    self.hass.async_create_task(
                        self._async_reload_requires_auth_entries(), eager_start=False
                    )
                    return self.async_abort(reason="reauth_successful")

        # Old config entries will not have these values.
        alias = entry_data.get(CONF_ALIAS) or "unknown"
        model = entry_data.get(CONF_MODEL) or "unknown"

        placeholders.update({"name": alias, "model": model, "host": host})

        self.context["title_placeholders"] = placeholders
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=STEP_AUTH_DATA_SCHEMA,
            errors=errors,
            description_placeholders=placeholders,
        )