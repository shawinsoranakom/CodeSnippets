async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a user defined configuration."""
        errors: dict[str, str] = {}

        if user_input is not None:
            if self.client_device_id is None:
                self.client_device_id = _generate_client_device_id()

            client = create_client(device_id=self.client_device_id)
            try:
                user_id, connect_result = await validate_input(
                    self.hass, user_input, client
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                errors["base"] = "unknown"
                _LOGGER.exception("Unexpected exception")
            else:
                entry_title = user_input[CONF_URL]

                server_info: dict[str, Any] = connect_result["Servers"][0]

                if server_name := server_info.get("Name"):
                    entry_title = server_name

                await self.async_set_unique_id(user_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=entry_title,
                    data={CONF_CLIENT_DEVICE_ID: self.client_device_id, **user_input},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                STEP_USER_DATA_SCHEMA, user_input
            ),
            errors=errors,
        )