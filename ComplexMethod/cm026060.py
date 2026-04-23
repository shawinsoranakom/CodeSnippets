async def async_step_user_auth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Dialog that informs the user that auth is required."""
        errors: dict[str, str] = {}
        if TYPE_CHECKING:
            # self.host is set by async_step_user and async_step_pick_device
            assert self.host is not None
        placeholders: dict[str, str] = {CONF_HOST: self.host}

        if user_input:
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]
            credentials = Credentials(username, password)
            device: Device | None
            try:
                if self._discovered_device:
                    device = await self._async_try_connect(
                        self._discovered_device, credentials
                    )
                else:
                    device = await self._async_try_connect_all(
                        self.host,
                        credentials=credentials,
                        raise_on_progress=False,
                        port=self.port,
                    )
            except AuthenticationError as ex:
                errors[CONF_PASSWORD] = "invalid_auth"
                placeholders["error"] = str(ex)
            except KasaException as ex:
                errors["base"] = "cannot_connect"
                placeholders["error"] = str(ex)
            else:
                if not device:
                    errors["base"] = "cannot_connect"
                    placeholders["error"] = "try_connect_all failed"
                else:
                    await set_credentials(self.hass, username, password)
                    self.hass.async_create_task(
                        self._async_reload_requires_auth_entries(), eager_start=False
                    )
                    if self._async_supports_camera_credentials(device):
                        return await self.async_step_camera_auth_confirm()

                    return self._async_create_or_update_entry_from_device(device)

        return self.async_show_form(
            step_id="user_auth_confirm",
            data_schema=STEP_AUTH_DATA_SCHEMA,
            errors=errors,
            description_placeholders=placeholders,
        )