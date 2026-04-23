async def async_step_user(
        self, user_input: dict[str, str] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        errors = {}
        if user_input is not None:
            self._async_abort_entries_match({CONF_HOST: user_input[CONF_HOST]})
            box = SFRBox(
                ip=user_input[CONF_HOST], client=async_get_clientsession(self.hass)
            )
            try:
                system_info = await box.system_get_info()
            except SFRBoxError:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "cannot_connect"
            else:
                if TYPE_CHECKING:
                    assert system_info is not None
                await self.async_set_unique_id(system_info.mac_addr)
                if self.source == SOURCE_RECONFIGURE:
                    self._abort_if_unique_id_mismatch()
                else:
                    self._abort_if_unique_id_configured()
                self._box = box
                self._config.update(user_input)
                return await self.async_step_choose_auth()

        suggested_values: Mapping[str, Any] | None = user_input
        if suggested_values is None and self.source == SOURCE_RECONFIGURE:
            suggested_values = self._get_reconfigure_entry().data
        data_schema = self.add_suggested_values_to_schema(DATA_SCHEMA, suggested_values)

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "sample_ip": "192.168.1.1",
                "sample_url": "https://sfrbox.example.com",
            },
        )