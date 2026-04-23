async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initiated by the user."""
        errors = {}
        if user_input is None and self.source == SOURCE_REAUTH:
            user_input = {CONF_ACCOUNT: self._get_reauth_entry().data[CONF_ACCOUNT]}
        elif user_input is not None:
            try:
                res = await self.hass.async_add_executor_job(validate_input, user_input)
                if res is not None:
                    name = str(res["personaname"])
                else:
                    errors["base"] = "invalid_account"
            except (steam.api.HTTPError, steam.api.HTTPTimeoutError) as ex:
                errors["base"] = "cannot_connect"
                if "403" in str(ex):
                    errors["base"] = "invalid_auth"
            except Exception as ex:  # noqa: BLE001
                LOGGER.exception("Unknown exception: %s", ex)
                errors["base"] = "unknown"
            if not errors:
                entry = await self.async_set_unique_id(user_input[CONF_ACCOUNT])
                if entry and self.source == SOURCE_REAUTH:
                    self.hass.config_entries.async_update_entry(entry, data=user_input)
                    await self.hass.config_entries.async_reload(entry.entry_id)
                    return self.async_abort(reason="reauth_successful")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=name,
                    data=user_input,
                    options={CONF_ACCOUNTS: {user_input[CONF_ACCOUNT]: name}},
                )
        user_input = user_input or {}
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_API_KEY, default=user_input.get(CONF_API_KEY) or ""
                    ): str,
                    vol.Required(
                        CONF_ACCOUNT, default=user_input.get(CONF_ACCOUNT) or ""
                    ): str,
                }
            ),
            errors=errors,
            description_placeholders=PLACEHOLDERS,
        )