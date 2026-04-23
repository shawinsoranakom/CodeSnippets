async def async_setup_entry(
    hass: HomeAssistant,
    entry: OpenDisplayConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up OpenDisplay event entities from binary_inputs device config."""
    coordinator = entry.runtime_data.coordinator

    descriptions: list[OpenDisplayEventEntityDescription] = []
    button_number = 0
    for bi in entry.runtime_data.device_config.binary_inputs:
        for button_id in range(8):  # input_flags is a bitmask over 8 pin slots
            if bi.input_flags & (1 << button_id):
                button_number += 1
                descriptions.append(
                    OpenDisplayEventEntityDescription(
                        key=f"button_{bi.instance_number}_{button_id}",
                        translation_key="button",
                        translation_placeholders={"number": str(button_number)},
                        device_class=EventDeviceClass.BUTTON,
                        event_types=["button_down", "button_up"],
                        byte_index=bi.button_data_byte_index,
                        button_id=button_id,
                    )
                )

    active_unique_ids = {f"{coordinator.address}-{d.key}" for d in descriptions}
    button_unique_id_prefix = f"{coordinator.address}-button_"
    entity_registry = er.async_get(hass)
    for entity_entry in er.async_entries_for_config_entry(
        entity_registry, entry.entry_id
    ):
        if (
            entity_entry.domain == "event"
            and entity_entry.unique_id.startswith(button_unique_id_prefix)
            and entity_entry.unique_id not in active_unique_ids
        ):
            entity_registry.async_remove(entity_entry.entity_id)

    async_add_entities(
        OpenDisplayEventEntity(coordinator, description) for description in descriptions
    )