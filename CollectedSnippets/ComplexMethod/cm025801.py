def _party_update_listener() -> None:
        """On party change, unload coordinator, remove device and reload."""
        nonlocal party, party_added_by_this_entry
        party_updated = coordinator.data.user.party.id

        if (
            party is not None and (party not in hass.data[HABITICA_KEY])
        ) or party != party_updated:
            if party_added_by_this_entry:
                config_entry.async_create_task(
                    hass, shutdown_party_coordinator(hass, party_added_by_this_entry)
                )
                party_added_by_this_entry = None
            if party:
                identifier = {(DOMAIN, f"{config_entry.unique_id}_{party!s}")}
                if device := device_reg.async_get_device(identifiers=identifier):
                    device_reg.async_update_device(
                        device.id, remove_config_entry_id=config_entry.entry_id
                    )

                notify_entities = [
                    entry.entity_id
                    for entry in entity_registry.entities.values()
                    if entry.domain == NOTIFY_DOMAIN
                    and entry.config_entry_id == config_entry.entry_id
                ]
                for entity_id in notify_entities:
                    entity_registry.async_remove(entity_id)

            hass.config_entries.async_schedule_reload(config_entry.entry_id)