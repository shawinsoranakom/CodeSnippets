async def async_step_dhcp_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle DHCP discovery confirmation - ask for credentials only."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Combine discovered host and device_id with user-provided password
            data = {
                CONF_HOST: self._discovered_host,
                CONF_USERNAME: self._discovered_device_id,
                CONF_PASSWORD: user_input[CONF_PASSWORD],
            }

            try:
                info = await validate_input(self.hass, data)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Store MAC address in config entry data
                if self._discovered_mac:
                    data[CONF_MAC] = self._discovered_mac

                return self.async_create_entry(title=info.title, data=data)

        # Only ask for password since we already have the device_id from discovery
        return self.async_show_form(
            step_id="dhcp_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            description_placeholders={
                "host": self._discovered_host or "",
                "device_id": self._discovered_device_id or "",
            },
            errors=errors,
        )