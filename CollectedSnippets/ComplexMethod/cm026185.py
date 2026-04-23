async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialised by the user."""

        errors = {}
        if self._com_ports_list is None:
            result = await async_scan_comports(self.hass)
            self._com_ports_list, self._default_com_port = result
            if self._default_com_port is None:
                return self.async_abort(reason="no_serial_ports")
            if TYPE_CHECKING:
                assert isinstance(self._com_ports_list, list)

        # Handle the initial step.
        if user_input is not None:
            try:
                info = await self.hass.async_add_executor_job(
                    validate_and_connect, self.hass, user_input
                )
            except OSError as error:
                if error.errno == 19:  # No such device.
                    errors["base"] = "invalid_serial_port"
            except AuroraError as error:
                if "could not open port" in str(error):
                    errors["base"] = "cannot_open_serial_port"
                elif "No response after" in str(error):
                    errors["base"] = "cannot_connect"  # could be dark
                else:
                    _LOGGER.error(
                        "Unable to communicate with Aurora ABB Inverter at %s: %s %s",
                        user_input[CONF_PORT],
                        type(error),
                        error,
                    )
                    errors["base"] = "cannot_connect"
            else:
                info.update(user_input)
                # Bomb out early if someone has already set up this device.
                device_unique_id = info["serial_number"]
                await self.async_set_unique_id(device_unique_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=info["title"], data=info)

        # If no user input, must be first pass through the config.  Show  initial form.
        config_options = {
            vol.Required(CONF_PORT, default=self._default_com_port): vol.In(
                self._com_ports_list
            ),
            vol.Required(CONF_ADDRESS, default=DEFAULT_ADDRESS): vol.In(
                range(MIN_ADDRESS, MAX_ADDRESS + 1)
            ),
        }
        schema = vol.Schema(config_options)

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)