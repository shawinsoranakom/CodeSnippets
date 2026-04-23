async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        device_options = await self._get_usb_devices()
        if user_input is not None:
            try:
                await self.hass.async_add_executor_job(
                    _validate_input,
                    user_input[CONF_DEVICE],
                    user_input[CONF_ID],
                    user_input[CONF_PASSWORD],
                )
            except MomongaSkScanFailure:
                errors["base"] = "cannot_connect"
            except MomongaSkJoinFailure:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(
                    user_input[CONF_ID], raise_on_progress=False
                )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=ENTRY_TITLE, data=user_input)

        discovered_device_id, discovered_device_name = (
            self._get_discovered_device_id_and_name(device_options)
        )
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_DEVICE, default=discovered_device_id): vol.In(
                        {discovered_device_id: discovered_device_name}
                        if discovered_device_id and discovered_device_name
                        else {
                            name: _human_readable_device_name(device)
                            for name, device in device_options.items()
                        }
                    ),
                    vol.Required(CONF_ID): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )