async def async_step_ssdp(
        self, discovery_info: SsdpServiceInfo
    ) -> ConfigFlowResult:
        """Handle a discovered UPnP/IGD device.

        This flow is triggered by the SSDP component. It will check if the
        host is already configured and delegate to the import step if not.
        """
        LOGGER.debug("async_step_ssdp: discovery_info: %s", discovery_info)

        # Ensure complete discovery.
        if not _is_complete_discovery(discovery_info):
            LOGGER.debug("Incomplete discovery, ignoring")
            return self.async_abort(reason="incomplete_discovery")

        # Ensure device is usable. Ideally we would use IgdDevice.is_profile_device,
        # but that requires constructing the device completely.
        if not _is_igd_device(discovery_info):
            LOGGER.debug("Non IGD device, ignoring")
            return self.async_abort(reason="non_igd_device")

        # Ensure not already configuring/configured.
        unique_id = discovery_info.ssdp_usn
        await self.async_set_unique_id(unique_id)
        mac_address = await _async_mac_address_from_discovery(self.hass, discovery_info)
        host = discovery_info.ssdp_headers["_host"]
        self._abort_if_unique_id_configured(
            # Store mac address and other data for older entries.
            # The location is stored in the config entry such that
            # when the location changes, the entry is reloaded.
            updates={
                CONFIG_ENTRY_MAC_ADDRESS: mac_address,
                CONFIG_ENTRY_LOCATION: get_preferred_location(
                    discovery_info.ssdp_all_locations
                ),
                CONFIG_ENTRY_HOST: host,
                CONFIG_ENTRY_ST: discovery_info.ssdp_st,
            },
        )

        # Handle devices changing their UDN, only allow a single host.
        for entry in self._async_current_entries(include_ignore=True):
            entry_mac_address = entry.data.get(CONFIG_ENTRY_MAC_ADDRESS)
            entry_host = entry.data.get(CONFIG_ENTRY_HOST)
            if entry_mac_address != mac_address and entry_host != host:
                continue

            entry_st = entry.data.get(CONFIG_ENTRY_ST)
            if discovery_info.ssdp_st != entry_st:
                # Check ssdp_st to prevent swapping between IGDv1 and IGDv2.
                continue

            if entry.source == SOURCE_IGNORE:
                # Host was already ignored. Don't update ignored entries.
                return self.async_abort(reason="discovery_ignored")

            LOGGER.debug("Updating entry: %s", entry.entry_id)
            return self.async_update_reload_and_abort(
                entry,
                unique_id=unique_id,
                data={**entry.data, CONFIG_ENTRY_UDN: discovery_info.ssdp_udn},
                reason="config_entry_updated",
            )

        # Store discovery.
        self._add_discovery(discovery_info)

        # Ensure user recognizable.
        self.context["title_placeholders"] = {
            "name": _friendly_name_from_discovery(discovery_info),
        }

        return await self.async_step_ssdp_confirm()