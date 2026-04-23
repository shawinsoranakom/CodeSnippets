def async_migrate_old_entity(
    hass: HomeAssistant,
    ent_reg: er.EntityRegistry,
    registered_unique_ids: set[str],
    platform: Platform,
    device: dr.DeviceEntry,
    unique_id: str,
) -> None:
    """Migrate existing entity if current one can't be found and an old one exists."""
    # If we can find an existing entity with this unique ID, there's nothing to migrate
    if ent_reg.async_get_entity_id(platform, DOMAIN, unique_id):
        return

    value_id = ValueID.from_unique_id(unique_id)

    # Look for existing entities in the registry that could be the same value but on
    # a different endpoint
    existing_entity_entries: list[er.RegistryEntry] = []
    for entry in er.async_entries_for_device(ent_reg, device.id):
        # If entity is not in the domain for this discovery info or entity has already
        # been processed, skip it
        if entry.domain != platform or entry.unique_id in registered_unique_ids:
            continue

        try:
            old_ent_value_id = ValueID.from_unique_id(entry.unique_id)
        # Skip non value ID based unique ID's (e.g. node status sensor)
        except IndexError:
            continue

        if value_id.is_same_value_different_endpoints(old_ent_value_id):
            existing_entity_entries.append(entry)
            # We can return early if we get more than one result
            if len(existing_entity_entries) > 1:
                return

    # If we couldn't find any results, return early
    if not existing_entity_entries:
        return

    entry = existing_entity_entries[0]
    state = hass.states.get(entry.entity_id)

    if not state or state.state == STATE_UNAVAILABLE:
        async_migrate_unique_id(ent_reg, platform, entry.unique_id, unique_id)