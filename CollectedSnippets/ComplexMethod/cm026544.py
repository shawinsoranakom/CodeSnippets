async def async_step_local_pick(
        self, user_input: Mapping[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle collecting and verifying Awair Local API hosts."""

        errors = {}

        # User input is either:
        # 1. None if first time on this step
        # 2. {device: manual} if picked manual entry option
        # 3. {device: <host>} if picked a device
        # 4. {host: <host>} if manually entered a host
        #
        # Option 1 and 2 will show the form again.
        if user_input and user_input.get(CONF_DEVICE) != "manual":
            if CONF_DEVICE in user_input:
                user_input = {CONF_HOST: user_input[CONF_DEVICE]}

            self._device, error = await self._check_local_connection(
                user_input.get(CONF_DEVICE) or user_input[CONF_HOST]
            )

            if self._device is not None:
                await self.async_set_unique_id(
                    self._device.mac_address, raise_on_progress=False
                )
                title = f"{self._device.model} ({self._device.device_id})"
                return self.async_create_entry(title=title, data=user_input)

            if error is not None:
                errors = {"base": error}

        discovered = self._get_discovered_entries()

        if not discovered or (user_input and user_input.get(CONF_DEVICE) == "manual"):
            data_schema = vol.Schema({vol.Required(CONF_HOST): str})

        elif discovered:
            discovered["manual"] = "Manual"
            data_schema = vol.Schema({vol.Required(CONF_DEVICE): vol.In(discovered)})

        return self.async_show_form(
            step_id="local_pick",
            data_schema=data_schema,
            errors=errors,
        )