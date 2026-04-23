async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=create_schema(user_input)
            )

        await self.async_set_unique_id(user_input[CONF_CLOUD_ID])
        errors = {}

        try:
            eagle_type, hardware_address = await async_get_type(
                self.hass,
                user_input[CONF_CLOUD_ID],
                user_input[CONF_INSTALL_CODE],
                user_input[CONF_HOST],
            )
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except Exception:
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            # Verify it is a known device, first
            if not eagle_type:
                errors["base"] = "unknown_device_type"
            elif eagle_type == TYPE_EAGLE_100:
                user_input[CONF_TYPE] = eagle_type

                # For EAGLE-100, there is no hardware address to select, so set it to None and move on
                user_input[CONF_HARDWARE_ADDRESS] = None
            elif eagle_type == TYPE_EAGLE_200:
                user_input[CONF_TYPE] = eagle_type

                # For EAGLE-200, a connected meter's hardware address is required to create the entry
                if not hardware_address:
                    # hardware_address will be None if there are no meters at all or if none are currently Connected
                    errors["base"] = "no_meters_connected"
                else:
                    user_input[CONF_HARDWARE_ADDRESS] = hardware_address
            else:
                # This is a device that isn't supported, yet, but was detected by async_get_type
                errors["base"] = "unsupported_device_type"

            # All information gathering is done, so if there are no errors at this point, create the entry
            if not errors:
                return self.async_create_entry(
                    title=user_input[CONF_CLOUD_ID], data=user_input
                )

        return self.async_show_form(
            step_id="user", data_schema=create_schema(user_input), errors=errors
        )