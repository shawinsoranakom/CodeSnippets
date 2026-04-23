async def _async_handle_discovery(self) -> ConfigFlowResult:
        """Handle any discovery."""
        device = self._discovered_device
        assert device is not None
        mac_address = device.mac
        mac = dr.format_mac(mac_address)
        host = device.ipaddress
        await self.async_set_unique_id(mac)
        for entry in self._async_current_entries(include_ignore=False):
            if entry.unique_id == mac or entry.data[CONF_HOST] == host:
                if (
                    async_update_entry_from_discovery(self.hass, entry, device)
                    and entry.state is not ConfigEntryState.SETUP_IN_PROGRESS
                ):
                    self.hass.config_entries.async_schedule_reload(entry.entry_id)
                return self.async_abort(reason="already_configured")
        self.host = host
        if self.hass.config_entries.flow.async_has_matching_flow(self):
            return self.async_abort(reason="already_in_progress")
        if not device.name:
            discovery = await async_discover_device(self.hass, device.ipaddress)
            if not discovery:
                return self.async_abort(reason="cannot_connect")
            self._discovered_device = discovery
        assert self._discovered_device is not None
        if not async_is_steamist_device(self._discovered_device):
            return self.async_abort(reason="not_steamist_device")
        return await self.async_step_discovery_confirm()