async def _async_set_discovered_mac(
        self, device: FluxLEDDiscovery, allow_update_mac: bool
    ) -> None:
        """Set the discovered mac.

        We only allow it to be updated if it comes from udp
        discovery since the dhcp mac can be one digit off from
        the udp discovery mac for devices with multiple network interfaces
        """
        mac_address = device[ATTR_ID]
        assert mac_address is not None
        mac = dr.format_mac(mac_address)
        await self.async_set_unique_id(mac)
        for entry in self._async_current_entries(include_ignore=True):
            if not (
                entry.data.get(CONF_HOST) == device[ATTR_IPADDR]
                or (
                    entry.unique_id
                    and ":" in entry.unique_id
                    and mac_matches_by_one(entry.unique_id, mac)
                )
            ):
                continue
            if entry.source == SOURCE_IGNORE:
                raise AbortFlow("already_configured")
            if (
                async_update_entry_from_discovery(
                    self.hass, entry, device, None, allow_update_mac
                )
                and entry.state
                not in (
                    ConfigEntryState.SETUP_IN_PROGRESS,
                    ConfigEntryState.NOT_LOADED,
                )
            ) or entry.state == ConfigEntryState.SETUP_RETRY:
                self.hass.config_entries.async_schedule_reload(entry.entry_id)
            else:
                async_dispatcher_send(
                    self.hass,
                    FLUX_LED_DISCOVERY_SIGNAL.format(entry_id=entry.entry_id),
                )
            raise AbortFlow("already_configured")