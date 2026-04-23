async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        placeholders: dict[str, str] = {}

        if user_input is not None:
            if not (host := user_input[CONF_HOST]):
                return await self.async_step_pick_device()

            host, port = self._async_get_host_port(host)

            match_dict: dict[str, Any] = {CONF_HOST: host}
            if port:
                self.port = port
                match_dict[CONF_PORT] = port
            self._async_abort_entries_match(match_dict)

            self.host = host
            credentials = await get_credentials(self.hass)
            try:
                device = await self._async_try_discover_and_update(
                    host,
                    credentials,
                    raise_on_progress=False,
                    raise_on_timeout=False,
                    port=port,
                ) or await self._async_try_connect_all(
                    host,
                    credentials=credentials,
                    raise_on_progress=False,
                    port=port,
                )
            except AuthenticationError:
                return await self.async_step_user_auth_confirm()
            except KasaException as ex:
                errors["base"] = "cannot_connect"
                placeholders["error"] = str(ex)
            else:
                if not device:
                    return await self.async_step_user_auth_confirm()

                if self._async_supports_camera_credentials(device):
                    return await self.async_step_camera_auth_confirm()

                return self._async_create_or_update_entry_from_device(device)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Optional(CONF_HOST, default=""): str}),
            errors=errors,
            description_placeholders=placeholders,
        )