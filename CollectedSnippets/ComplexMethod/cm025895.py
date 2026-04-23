async def async_step_init(
        self, user_input: dict[str, dict[str, str]] | None = None
    ) -> ConfigFlowResult:
        """Manage Steam options."""
        if user_input is not None:
            await self.hass.config_entries.async_unload(self.config_entry.entry_id)
            for _id in self.options[CONF_ACCOUNTS]:
                if _id not in user_input[CONF_ACCOUNTS] and (
                    entity_id := er.async_get(self.hass).async_get_entity_id(
                        Platform.SENSOR, DOMAIN, f"sensor.steam_{_id}"
                    )
                ):
                    er.async_get(self.hass).async_remove(entity_id)
            channel_data = {
                CONF_ACCOUNTS: {
                    _id: name
                    for _id, name in self.options[CONF_ACCOUNTS].items()
                    if _id in user_input[CONF_ACCOUNTS]
                }
            }
            await self.hass.config_entries.async_reload(self.config_entry.entry_id)
            return self.async_create_entry(title="", data=channel_data)
        error = None
        try:
            users = {
                name["steamid"]: name["personaname"]
                for name in await self.hass.async_add_executor_job(self.get_accounts)
            }
            if not users:
                error = {"base": "unauthorized"}

        except steam.api.HTTPTimeoutError:
            users = self.options[CONF_ACCOUNTS]

        options = {
            vol.Required(
                CONF_ACCOUNTS,
                default=set(self.options[CONF_ACCOUNTS]),
            ): cv.multi_select(users | self.options[CONF_ACCOUNTS]),
        }
        self.options[CONF_ACCOUNTS] = users | self.options[CONF_ACCOUNTS]

        return self.async_show_form(
            step_id="init", data_schema=vol.Schema(options), errors=error
        )