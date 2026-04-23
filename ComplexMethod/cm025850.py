async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            session = async_create_clientsession(self.hass)
            api = CompitApiConnector(session)
            success = False
            try:
                success = await api.init(
                    user_input[CONF_EMAIL],
                    user_input[CONF_PASSWORD],
                    self.hass.config.language,
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                if not success:
                    # Api returned unexpected result but no exception
                    _LOGGER.error("Compit api returned unexpected result")
                    errors["base"] = "unknown"
                else:
                    await self.async_set_unique_id(user_input[CONF_EMAIL])

                    if self.source == SOURCE_REAUTH:
                        self._abort_if_unique_id_mismatch()
                        return self.async_update_reload_and_abort(
                            self._get_reauth_entry(), data_updates=user_input
                        )
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=user_input[CONF_EMAIL], data=user_input
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            description_placeholders={"compit_url": "https://inext.compit.pl/"},
        )