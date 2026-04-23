async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        errors: dict[str, str] = {}
        if user_input is None:
            return self.async_show_form_step_user(errors)

        self.interface = user_input[CONF_INTERFACE]

        # allow optional manual setting of host and mac
        if self.host is None:
            self.host = user_input.get(CONF_HOST)
        if self.sid is None:
            # format sid from mac_address
            if (mac_address := user_input.get(CONF_MAC)) is not None:
                self.sid = format_mac(mac_address).replace(":", "")

        # if host is already known by zeroconf discovery or manual optional settings
        if self.host is not None and self.sid is not None:
            # Connect to Xiaomi Aqara Gateway
            self.selected_gateway = await self.hass.async_add_executor_job(
                XiaomiGateway,
                self.host,
                self.sid,
                None,
                DEFAULT_DISCOVERY_RETRY,
                self.interface,
                MULTICAST_PORT,
                None,
            )

            if self.selected_gateway.connection_error:
                errors[CONF_HOST] = "invalid_host"
            if self.selected_gateway.mac_error:
                errors[CONF_MAC] = "invalid_mac"
            if errors:
                return self.async_show_form_step_user(errors)

            return await self.async_step_settings()

        # Discover Xiaomi Aqara Gateways in the network to get required SIDs.
        xiaomi = XiaomiGatewayDiscovery(self.interface)
        try:
            await self.hass.async_add_executor_job(xiaomi.discover_gateways)
        except gaierror:
            errors[CONF_INTERFACE] = "invalid_interface"
            return self.async_show_form_step_user(errors)

        self.gateways = xiaomi.gateways

        if len(self.gateways) == 1:
            self.selected_gateway = list(self.gateways.values())[0]
            self.sid = self.selected_gateway.sid
            return await self.async_step_settings()
        if len(self.gateways) > 1:
            return await self.async_step_select()

        errors["base"] = "discovery_error"
        return self.async_show_form_step_user(errors)