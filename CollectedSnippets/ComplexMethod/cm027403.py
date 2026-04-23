def handle_device_event(ev: Event[EventDeviceRegistryUpdatedData]) -> None:
        """Enable the online status entity for the mac of a newly created device."""
        # Only for new devices
        if ev.data["action"] != "create":
            return

        dev_reg = dr.async_get(hass)
        device_entry = dev_reg.async_get(ev.data["device_id"])

        if device_entry is None:
            # This should not happen, since the device was just created.
            return

        # Check if device has a mac
        mac = None
        for conn in device_entry.connections:
            if conn[0] == dr.CONNECTION_NETWORK_MAC:
                mac = conn[1]
                break

        if mac is None:
            return

        # Check if we have an entity for this mac
        if (unique_id := data.get(mac)) is None:
            return

        ent_reg = er.async_get(hass)

        if (entity_id := ent_reg.async_get_entity_id(DOMAIN, *unique_id)) is None:
            return

        entity_entry = ent_reg.entities[entity_id]

        # Make sure entity has a config entry and was disabled by the
        # default disable logic in the integration and new entities
        # are allowed to be added.
        if (
            entity_entry.config_entry_id is None
            or (
                (
                    config_entry := hass.config_entries.async_get_entry(
                        entity_entry.config_entry_id
                    )
                )
                is not None
                and config_entry.pref_disable_new_entities
            )
            or entity_entry.disabled_by != er.RegistryEntryDisabler.INTEGRATION
        ):
            return

        # Enable entity
        ent_reg.async_update_entity(entity_id, disabled_by=None)