async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        errors: dict[str, str] = {}
        if user_input:
            session = async_get_clientsession(self.hass)
            self.client = AirGradientClient(user_input[CONF_HOST], session=session)
            try:
                current_measures = await self.client.get_current_measures()
            except AirGradientParseError:
                return self.async_abort(reason="invalid_version")
            except AirGradientError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(
                    current_measures.serial_number, raise_on_progress=False
                )
                if self.source == SOURCE_USER:
                    self._abort_if_unique_id_configured()
                if self.source == SOURCE_RECONFIGURE:
                    self._abort_if_unique_id_mismatch()
                await self.set_configuration_source()
                if self.source == SOURCE_USER:
                    return self.async_create_entry(
                        title=current_measures.model,
                        data={CONF_HOST: user_input[CONF_HOST]},
                    )
                return self.async_update_reload_and_abort(
                    self._get_reconfigure_entry(),
                    data={CONF_HOST: user_input[CONF_HOST]},
                )
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_HOST): str}),
            errors=errors,
        )