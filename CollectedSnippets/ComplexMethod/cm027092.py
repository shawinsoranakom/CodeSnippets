async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initiated by the user."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self.host = user_input[CONF_HOST]
            self.protocol = user_input[CONF_PROTOCOL]
            if self.protocol == "rest_api":
                # Check if authentication is required.
                try:
                    device_info = await test_rest_api_connection(self.host, user_input)
                except CannotConnect:
                    errors["base"] = "cannot_connect"
                except NotAuthorised:
                    # Proceed to authentication step.
                    return await self.async_step_authentication()
                except UnknownException:
                    errors["base"] = "unknown"
                    # If the connection was not successful, show an error.

                # If the connection was successful, create the device.
                if not errors:
                    return await self._create_entry(
                        host=self.host,
                        protocol=self.protocol,
                        device_info=device_info,
                        user_input=user_input,
                    )

            if self.protocol == "modbus_tcp":
                # Proceed to modbus step.
                return await self.async_step_modbus_tcp()

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )