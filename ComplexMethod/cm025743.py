async def _async_handle_discovery(self) -> ConfigFlowResult:
        """Handle any discovery."""
        device = self._discovered_device
        assert device is not None
        mac = dr.format_mac(device.mac_address)
        host = device.ip_address
        await self.async_set_unique_id(mac)
        for entry in self._async_current_entries(include_ignore=False):
            if (
                entry.unique_id == mac
                or hostname_from_url(entry.data[CONF_HOST]) == host
            ):
                if async_update_entry_from_discovery(self.hass, entry, device):
                    self.hass.config_entries.async_schedule_reload(entry.entry_id)
                return self.async_abort(reason="already_configured")
        self.host = host
        if self.hass.config_entries.flow.async_has_matching_flow(self):
            return self.async_abort(reason="already_in_progress")
        # Handled ignored case since _async_current_entries
        # is called with include_ignore=False
        self._abort_if_unique_id_configured()
        if not device.port:
            if discovered_device := await async_discover_device(self.hass, host):
                self._discovered_device = discovered_device
            else:
                return self.async_abort(reason="cannot_connect")
        return await self.async_step_discovery_confirm()