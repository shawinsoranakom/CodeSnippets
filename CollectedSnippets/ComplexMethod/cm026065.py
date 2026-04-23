async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Trigger a reconfiguration flow."""
        errors: dict[str, str] = {}
        placeholders: dict[str, str] = {}

        reconfigure_entry = self._get_reconfigure_entry()
        assert reconfigure_entry.unique_id
        await self.async_set_unique_id(reconfigure_entry.unique_id)

        host = reconfigure_entry.data[CONF_HOST]
        port = reconfigure_entry.data.get(CONF_PORT)

        if user_input is not None:
            host, port = self._async_get_host_port(host)

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
            except AuthenticationError:  # Error from the update()
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
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                STEP_RECONFIGURE_DATA_SCHEMA,
                {CONF_HOST: f"{host}:{port}" if port else host},
            ),
            errors=errors,
            description_placeholders={
                **placeholders,
                CONF_MAC: reconfigure_entry.unique_id,
            },
        )