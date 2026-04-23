async def async_call_deconz_service(service_call: ServiceCall) -> None:
        """Call correct deCONZ service."""
        service = service_call.service
        service_data = service_call.data

        if CONF_BRIDGE_ID in service_data:
            found_hub = False
            bridge_id = normalize_bridge_id(service_data[CONF_BRIDGE_ID])

            entry: DeconzConfigEntry
            for entry in hass.config_entries.async_loaded_entries(DOMAIN):
                possible_hub = entry.runtime_data
                if possible_hub.bridgeid == bridge_id:
                    hub = possible_hub
                    found_hub = True
                    break

            if not found_hub:
                LOGGER.error("Could not find the gateway %s", bridge_id)
                return
        else:
            try:
                hub = get_master_hub(hass)
            except ValueError:
                LOGGER.error("No master gateway available")
                return

        if service == SERVICE_CONFIGURE_DEVICE:
            await async_configure_service(hub, service_data)

        elif service == SERVICE_DEVICE_REFRESH:
            await async_refresh_devices_service(hub)

        elif service == SERVICE_REMOVE_ORPHANED_ENTRIES:
            await async_remove_orphaned_entries_service(hub)