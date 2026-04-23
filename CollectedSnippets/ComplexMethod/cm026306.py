async def async_step_integration_discovery(
        self, discovery_info: DiscoveryInfoType
    ) -> ConfigFlowResult:
        """Handle integration discovery."""
        self._discovered_device = discovery_info
        mac = _async_unifi_mac_from_hass(discovery_info["hw_addr"])
        await self.async_set_unique_id(mac)
        source_ip = discovery_info["source_ip"]
        direct_connect_domain = discovery_info["direct_connect_domain"]
        for entry in self._async_current_entries():
            if entry.source == SOURCE_IGNORE:
                if entry.unique_id == mac:
                    return self.async_abort(reason="already_configured")
                continue
            entry_host = entry.data[CONF_HOST]
            entry_has_direct_connect = _host_is_direct_connect(entry_host)
            if entry.unique_id == mac:
                new_host = None
                if (
                    entry_has_direct_connect
                    and direct_connect_domain
                    and entry_host != direct_connect_domain
                ):
                    new_host = direct_connect_domain
                elif (
                    not entry_has_direct_connect
                    and is_ip_address(entry_host)
                    and entry_host != source_ip
                    and await _async_console_is_offline(self.hass, entry)
                ):
                    new_host = source_ip
                if new_host:
                    self.hass.config_entries.async_update_entry(
                        entry, data={**entry.data, CONF_HOST: new_host}
                    )
                return self.async_abort(reason="already_configured")
            if entry_host in (direct_connect_domain, source_ip) or (
                entry_has_direct_connect
                and (ip := await _async_resolve(self.hass, entry_host))
                and ip == source_ip
            ):
                return self.async_abort(reason="already_configured")
        return await self.async_step_discovery_confirm()