async def async_step_auth(
        self, user_input: dict[str, str] | None = None
    ) -> ConfigFlowResult:
        """Check authentication."""
        errors = {}
        if user_input is not None:
            try:
                await self._box.authenticate(
                    username=user_input[CONF_USERNAME],
                    password=user_input[CONF_PASSWORD],
                )
            except SFRBoxAuthenticationError:
                errors["base"] = "invalid_auth"
            else:
                if self.source == SOURCE_REAUTH:
                    return self.async_update_reload_and_abort(
                        self._get_reauth_entry(), data_updates=user_input
                    )
                self._config.update(user_input)
                if self.source == SOURCE_RECONFIGURE:
                    return self.async_update_reload_and_abort(
                        self._get_reconfigure_entry(), data=self._config
                    )
                return self.async_create_entry(title="SFR Box", data=self._config)

        suggested_values: Mapping[str, Any] | None = user_input
        if suggested_values is None:
            if self.source == SOURCE_REAUTH:
                suggested_values = self._get_reauth_entry().data
            elif self.source == SOURCE_RECONFIGURE:
                suggested_values = self._get_reconfigure_entry().data

        data_schema = self.add_suggested_values_to_schema(AUTH_SCHEMA, suggested_values)
        return self.async_show_form(
            step_id="auth", data_schema=data_schema, errors=errors
        )