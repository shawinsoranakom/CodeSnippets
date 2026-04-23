async def _async_handle_discovery(self) -> ConfigFlowResult:
        """Handle any discovery."""
        device = self._discovered_device
        assert device is not None
        await self._async_set_discovered_mac(device, self._allow_update_mac)
        host = device[ATTR_IPADDR]
        self.host = host
        if self.hass.config_entries.flow.async_has_matching_flow(self):
            return self.async_abort(reason="already_in_progress")
        if not device[ATTR_MODEL_DESCRIPTION]:
            mac_address = device[ATTR_ID]
            assert mac_address is not None
            mac = dr.format_mac(mac_address)
            try:
                device = await self._async_try_connect(host, device)
            except FLUX_LED_EXCEPTIONS:
                return self.async_abort(reason="cannot_connect")

            discovered_mac = device[ATTR_ID]
            if device[ATTR_MODEL_DESCRIPTION] or (
                discovered_mac is not None
                and (formatted_discovered_mac := dr.format_mac(discovered_mac))
                and formatted_discovered_mac != mac
                and mac_matches_by_one(discovered_mac, mac)
            ):
                self._discovered_device = device
                await self._async_set_discovered_mac(device, True)
        return await self.async_step_discovery_confirm()