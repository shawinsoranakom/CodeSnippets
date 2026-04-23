async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """First step in the config flow."""
        errors = {}

        if user_input is not None:
            ip_address = user_input[CONF_HOST]
            guid: str | None = None

            main_repeater = Lutron(
                ip_address,
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
            )

            try:
                await self.hass.async_add_executor_job(main_repeater.load_xml_db)
            except HTTPError:
                _LOGGER.exception("Http error")
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unknown error")
                errors["base"] = "unknown"
            else:
                guid = main_repeater.guid

                if guid is None or len(guid) <= 10:
                    errors["base"] = "cannot_connect"

            if not errors:
                assert guid is not None
                await self.async_set_unique_id(guid)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title="Lutron", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_USERNAME, default="lutron"): str,
                    vol.Required(CONF_PASSWORD, default="integration"): str,
                }
            ),
            errors=errors,
        )