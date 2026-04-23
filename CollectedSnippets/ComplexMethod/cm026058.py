async def async_step_discovery_auth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Dialog that informs the user that auth is required."""
        assert self._discovered_device is not None
        errors = {}

        credentials = await get_credentials(self.hass)
        if credentials and credentials != self._discovered_device.config.credentials:
            try:
                device = await self._async_try_connect(
                    self._discovered_device, credentials
                )
            except AuthenticationError:
                pass  # Authentication exceptions should continue to the rest of the step
            else:
                self._discovered_device = device
                return await self.async_step_discovery_confirm()

        placeholders = self._async_make_placeholders_from_discovery()

        if user_input:
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]
            credentials = Credentials(username, password)
            try:
                device = await self._async_try_connect(
                    self._discovered_device, credentials
                )
            except AuthenticationError as ex:
                errors[CONF_PASSWORD] = "invalid_auth"
                placeholders["error"] = str(ex)
            except KasaException as ex:
                errors["base"] = "cannot_connect"
                placeholders["error"] = str(ex)
            else:
                self._discovered_device = device
                await set_credentials(self.hass, username, password)
                self.hass.async_create_task(
                    self._async_reload_requires_auth_entries(), eager_start=False
                )
                if self._async_supports_camera_credentials(device):
                    return await self.async_step_camera_auth_confirm()

                return self._async_create_or_update_entry_from_device(
                    self._discovered_device
                )

        self.context["title_placeholders"] = placeholders
        return self.async_show_form(
            step_id="discovery_auth_confirm",
            data_schema=STEP_AUTH_DATA_SCHEMA,
            errors=errors,
            description_placeholders=placeholders,
        )