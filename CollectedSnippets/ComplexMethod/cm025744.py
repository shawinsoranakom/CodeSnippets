async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfiguration of the integration."""
        errors: dict[str, str] = {}
        reconfigure_entry = self._get_reconfigure_entry()
        existing_data = reconfigure_entry.data

        if user_input is not None:
            validate_input_data = dict(user_input)
            validate_input_data[CONF_PREFIX] = existing_data.get(CONF_PREFIX, "")

            try:
                info = await validate_input(
                    validate_input_data, reconfigure_entry.unique_id
                )
            except TimeoutError:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors[CONF_PASSWORD] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception during reconfiguration")
                errors["base"] = "unknown"
            else:
                # Discover the device at the provided address to obtain its MAC (unique_id)
                device = await async_discover_device(
                    self.hass, validate_input_data[CONF_ADDRESS]
                )
                if device is not None and device.mac_address:
                    await self.async_set_unique_id(dr.format_mac(device.mac_address))
                    self._abort_if_unique_id_mismatch()  # aborts if user tried to switch devices
                else:
                    # If we cannot confirm identity, keep existing behavior (don't block reconfigure)
                    await self.async_set_unique_id(reconfigure_entry.unique_id)

                return self.async_update_reload_and_abort(
                    reconfigure_entry,
                    data_updates={
                        **reconfigure_entry.data,
                        CONF_HOST: info[CONF_HOST],
                        CONF_USERNAME: validate_input_data[CONF_USERNAME],
                        CONF_PASSWORD: validate_input_data[CONF_PASSWORD],
                        CONF_PREFIX: info[CONF_PREFIX],
                    },
                    reason="reconfigure_successful",
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_USERNAME,
                        default=existing_data.get(CONF_USERNAME, ""),
                    ): str,
                    vol.Optional(
                        CONF_PASSWORD,
                        default="",
                    ): str,
                    vol.Required(
                        CONF_ADDRESS,
                        default=hostname_from_url(existing_data[CONF_HOST]),
                    ): str,
                    vol.Required(
                        CONF_PROTOCOL,
                        default=_get_protocol_from_url(existing_data[CONF_HOST]),
                    ): vol.In(ALL_PROTOCOLS),
                }
            ),
            errors=errors,
        )