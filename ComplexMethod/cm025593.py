async def async_step_dhcp(
        self, discovery_info: DhcpServiceInfo
    ) -> ConfigFlowResult:
        """Handle discovery via dhcp."""
        mac_address = format_mac(discovery_info.macaddress)
        existing_entry = await self.async_set_unique_id(mac_address)
        if existing_entry and CONF_HOST not in existing_entry.data:
            _LOGGER.debug(
                "Reolink DHCP discovered device with MAC '%s' and IP '%s', "
                "but existing config entry does not have host, ignoring",
                mac_address,
                discovery_info.ip,
            )
            raise AbortFlow("already_configured")

        if (
            existing_entry
            and CONF_PASSWORD in existing_entry.data
            and existing_entry.data[CONF_HOST] != discovery_info.ip
        ):
            if is_connected(self.hass, existing_entry):
                _LOGGER.debug(
                    "Reolink DHCP reported new IP '%s', "
                    "but connection to camera seems to be okay, so sticking to IP '%s'",
                    discovery_info.ip,
                    existing_entry.data[CONF_HOST],
                )
                raise AbortFlow("already_configured")

            # check if the camera is reachable at the new IP
            new_config = dict(existing_entry.data)
            new_config[CONF_HOST] = discovery_info.ip
            host = ReolinkHost(self.hass, new_config, existing_entry.options)
            try:
                await host.api.get_state("GetLocalLink")
                await host.api.logout()
            except ReolinkError as err:
                _LOGGER.debug(
                    "Reolink DHCP reported new IP '%s', "
                    "but got error '%s' trying to connect, so sticking to IP '%s'",
                    discovery_info.ip,
                    err,
                    existing_entry.data[CONF_HOST],
                )
                raise AbortFlow("already_configured") from err
            if format_mac(host.api.mac_address) != mac_address:
                _LOGGER.debug(
                    "Reolink mac address '%s' at new IP '%s' from DHCP, "
                    "does not match mac '%s' of config entry, so sticking to IP '%s'",
                    format_mac(host.api.mac_address),
                    discovery_info.ip,
                    mac_address,
                    existing_entry.data[CONF_HOST],
                )
                raise AbortFlow("already_configured")

        if existing_entry and existing_entry.data[CONF_HOST] != discovery_info.ip:
            _LOGGER.debug(
                "Reolink DHCP reported new IP '%s', updating from old IP '%s'",
                discovery_info.ip,
                existing_entry.data[CONF_HOST],
            )

        self._abort_if_unique_id_configured(updates={CONF_HOST: discovery_info.ip})

        self.context["title_placeholders"] = {
            "ip_address": discovery_info.ip,
            "hostname": discovery_info.hostname,
        }

        self._host = discovery_info.ip
        return await self.async_step_user()