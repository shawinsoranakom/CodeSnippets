def async_remove_orphaned_entities(
    hass: HomeAssistant,
    config_entry_id: str,
    mac: str,
    platform: str,
    keys: Iterable[str],
    key_suffix: str | None = None,
) -> None:
    """Remove orphaned entities."""
    orphaned_entities = []
    entity_reg = er.async_get(hass)

    entities = er.async_entries_for_config_entry(entity_reg, config_entry_id)
    for entity in entities:
        if not entity.entity_id.startswith(platform):
            continue
        if key_suffix is not None and key_suffix not in entity.unique_id:
            continue
        # we are looking for the component ID, e.g. boolean:201, em1data:1
        if not (match := COMPONENT_ID_PATTERN.search(entity.unique_id)):
            continue

        key = match.group()
        if key not in keys:
            LOGGER.debug(
                "Found orphaned Shelly entity: %s, unique id: %s",
                entity.entity_id,
                entity.unique_id,
            )
            orphaned_entities.append(entity.unique_id.split("-", 1)[1])

    if orphaned_entities:
        async_remove_shelly_rpc_entities(hass, platform, mac, orphaned_entities)