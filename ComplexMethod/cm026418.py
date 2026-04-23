async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow start."""
        # Check if user chooses manual entry
        if user_input is not None and not user_input.get(CONF_HOST):
            return await self.async_step_manual()

        if (
            user_input is not None
            and self.discovered_robots is not None
            and user_input[CONF_HOST] in self.discovered_robots
        ):
            self.host = user_input[CONF_HOST]
            return await self._async_start_link()

        already_configured = self._async_current_ids(False)

        devices = await _async_discover_roombas(self.hass, self.host)

        if devices:
            # Find already configured hosts
            self.discovered_robots = {
                device.ip: device
                for device in devices
                if device.blid not in already_configured
            }

        if self.host and self.host in self.discovered_robots:
            # From discovery
            self.context["title_placeholders"] = {
                "host": self.host,
                "name": self.discovered_robots[self.host].robot_name,
            }
            return await self._async_start_link()

        if not self.discovered_robots:
            return await self.async_step_manual()

        hosts: dict[str | None, str] = {
            **{
                device.ip: f"{device.robot_name} ({device.ip})"
                for device in devices
                if device.blid not in already_configured
            },
            None: "Manually add a Roomba or Braava",
        }

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Optional("host"): vol.In(hosts)}),
        )