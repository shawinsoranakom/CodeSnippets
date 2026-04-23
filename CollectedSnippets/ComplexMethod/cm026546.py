async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAccessToken:
                errors["base"] = "invalid_access_token"
            except InvalidHost:
                errors["base"] = "invalid_host"
            except TimeoutConnect:
                errors["base"] = "timeout_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                user_input[CONF_MAC] = info["mac"]
                await self.async_set_unique_id(dr.format_mac(info["mac"]))
                self._abort_if_unique_id_configured(updates=user_input)
                return self.async_create_entry(title="Rabbit Air", data=user_input)

        user_input = user_input or {}
        host = user_input.get(CONF_HOST, self._discovered_host)
        token = user_input.get(CONF_ACCESS_TOKEN)
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=host): str,
                    vol.Required(CONF_ACCESS_TOKEN, default=token): vol.All(
                        str, vol.Length(min=32, max=32)
                    ),
                }
            ),
            errors=errors,
        )