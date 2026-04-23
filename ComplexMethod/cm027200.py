async def async_step_pin(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle PIN authorize step."""
        errors: dict[str, str] = {}
        client_id, nickname = await self.gen_instance_ids()

        if user_input is not None:
            self.device_config[CONF_PIN] = user_input[CONF_PIN]
            self.device_config[CONF_CLIENT_ID] = client_id
            self.device_config[CONF_NICKNAME] = nickname
            try:
                if self.source == SOURCE_REAUTH:
                    return await self.async_reauth_device()
                return await self.async_create_device()
            except BraviaAuthError:
                errors["base"] = "invalid_auth"
            except BraviaNotSupported:
                errors["base"] = "unsupported_model"
            except BraviaError:
                errors["base"] = "cannot_connect"

        assert self.client

        try:
            await self.client.pair(client_id, nickname)
        except BraviaError:
            return self.async_abort(reason="no_ip_control")

        return self.async_show_form(
            step_id="pin",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PIN): str,
                }
            ),
            errors=errors,
        )