async def async_step_dhcp(
        self, discovery_info: DhcpServiceInfo
    ) -> ConfigFlowResult:
        """Handle dhcp discovery."""
        self.ip_address = discovery_info.ip
        gateway_din = discovery_info.hostname.upper()
        # The hostname is the gateway_din (unique_id)
        await self.async_set_unique_id(gateway_din)
        for entry in self._async_current_entries(include_ignore=False):
            if entry.data[CONF_IP_ADDRESS] == discovery_info.ip:
                if entry.unique_id is not None and is_ip_address(entry.unique_id):
                    if self.hass.config_entries.async_update_entry(
                        entry, unique_id=gateway_din
                    ):
                        self.hass.config_entries.async_schedule_reload(entry.entry_id)
                return self.async_abort(reason="already_configured")
            if entry.unique_id == gateway_din:
                if await self._async_powerwall_is_offline(entry):
                    if self.hass.config_entries.async_update_entry(
                        entry, data={**entry.data, CONF_IP_ADDRESS: self.ip_address}
                    ):
                        self.hass.config_entries.async_schedule_reload(entry.entry_id)
                return self.async_abort(reason="already_configured")
        # Still need to abort for ignored entries
        self._abort_if_unique_id_configured()
        self.context["title_placeholders"] = {
            "name": gateway_din,
            "ip_address": self.ip_address,
        }
        errors, info, _ = await self._async_try_connect(
            {CONF_IP_ADDRESS: self.ip_address, CONF_PASSWORD: gateway_din[-5:]}
        )
        if errors:
            if CONF_PASSWORD in errors:
                # The default password is the gateway din last 5
                # if it does not work, we have to ask
                return await self.async_step_user()
            return self.async_abort(reason="cannot_connect")
        assert info is not None
        self.title = info["title"]
        return await self.async_step_confirm_discovery()