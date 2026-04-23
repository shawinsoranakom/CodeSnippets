def _async_setup_block_entry(
    hass: HomeAssistant,
    config_entry: ShellyConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up entities for BLOCK device."""
    entities: list[ShellyBlockEvent] = []

    coordinator = config_entry.runtime_data.block
    if TYPE_CHECKING:
        assert coordinator and coordinator.device.blocks

    for block in coordinator.device.blocks:
        if (
            "inputEvent" not in block.sensor_ids
            or "inputEventCnt" not in block.sensor_ids
        ):
            continue

        if BLOCK_EVENT.removal_condition and BLOCK_EVENT.removal_condition(
            coordinator.device.settings, block
        ):
            channel = int(block.channel or 0) + 1
            unique_id = f"{coordinator.mac}-{block.description}-{channel}"
            async_remove_shelly_entity(hass, EVENT_DOMAIN, unique_id)
        else:
            entities.append(ShellyBlockEvent(coordinator, block, BLOCK_EVENT))

    async_add_entities(entities)