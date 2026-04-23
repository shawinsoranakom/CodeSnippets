async def async_step_select_gateway(
        self, discovery_info: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle gateway discovery."""
        errors: dict[str, str] = {}

        if discovery_info and "selected_gateway" in discovery_info:
            selected_sn = discovery_info["selected_gateway"]
            selected_gateway = self._discovered_gateways[selected_sn]

            await self.async_set_unique_id(selected_gateway.gw_sn)
            self._abort_if_unique_id_configured()

            try:
                await selected_gateway.connect()
            except DaliGatewayError as err:
                _LOGGER.debug(
                    "Failed to connect to gateway %s during config flow",
                    selected_gateway.gw_sn,
                    exc_info=err,
                )
                errors["base"] = "cannot_connect"
            else:
                await selected_gateway.disconnect()
                return self.async_create_entry(
                    title=selected_gateway.name,
                    data={
                        CONF_SERIAL_NUMBER: selected_gateway.gw_sn,
                        CONF_HOST: selected_gateway.gw_ip,
                        CONF_PORT: selected_gateway.port,
                        CONF_NAME: selected_gateway.name,
                        CONF_USERNAME: selected_gateway.username,
                        CONF_PASSWORD: selected_gateway.passwd,
                    },
                )

        if not self._discovered_gateways:
            _LOGGER.debug("Starting gateway discovery")
            discovery = DaliGatewayDiscovery()
            try:
                discovered = await discovery.discover_gateways()
            except DaliGatewayError as err:
                _LOGGER.debug("Gateway discovery failed", exc_info=err)
                errors["base"] = "discovery_failed"
            else:
                configured_gateways = {
                    entry.data[CONF_SERIAL_NUMBER]
                    for entry in self.hass.config_entries.async_entries(DOMAIN)
                }

                self._discovered_gateways = {
                    gw.gw_sn: gw
                    for gw in discovered
                    if gw.gw_sn not in configured_gateways
                }

        if not self._discovered_gateways:
            return self.async_show_form(
                step_id="select_gateway",
                errors=errors or {"base": "no_devices_found"},
                data_schema=vol.Schema({}),
            )

        gateway_options = [
            SelectOptionDict(
                value=sn,
                label=f"{gateway.name} [SN {sn}, IP {gateway.gw_ip}]",
            )
            for sn, gateway in self._discovered_gateways.items()
        ]

        return self.async_show_form(
            step_id="select_gateway",
            data_schema=vol.Schema(
                {
                    vol.Optional("selected_gateway"): SelectSelector(
                        SelectSelectorConfig(options=gateway_options, sort=True)
                    ),
                }
            ),
            errors=errors,
        )