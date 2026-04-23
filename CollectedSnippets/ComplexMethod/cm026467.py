async def async_step_cloud_select_device(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle device selection from devices offered by the cloud."""
        if self.discovered:
            user_input = {CONF_DEVICE: self.discovered_serial}
        elif self.source == SOURCE_REAUTH:
            reauth_unique_id = self._get_reauth_entry().unique_id
            if reauth_unique_id not in self.devices:
                return self.async_abort(reason="reauth_device_not_found")
            user_input = {CONF_DEVICE: reauth_unique_id}
        elif len(self.devices) == 1:
            user_input = {CONF_DEVICE: list(self.devices.values())[0].serial_number}

        errors: dict[str, str] = {}
        if user_input is not None:
            device = self.devices[user_input[CONF_DEVICE]]
            try:
                return await self._async_step_create_entry(
                    str(device.ip), device.api_key
                )
            except AbortFlow:
                raise
            except LaMetricConnectionError as ex:
                LOGGER.error("Error connecting to LaMetric: %s", ex)
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                LOGGER.exception("Unexpected error occurred")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="cloud_select_device",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_DEVICE): SelectSelector(
                        SelectSelectorConfig(
                            mode=SelectSelectorMode.DROPDOWN,
                            options=[
                                SelectOptionDict(
                                    value=device.serial_number,
                                    label=device.name,
                                )
                                for device in self.devices.values()
                            ],
                        )
                    ),
                }
            ),
            errors=errors,
        )