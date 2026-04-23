async def async_setup_entry(
    hass: HomeAssistant,
    entry: PlenticoreConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add kostal plenticore Select widget."""
    plenticore = entry.runtime_data

    available_settings_data = await plenticore.client.get_settings()
    select_data_update_coordinator = SelectDataUpdateCoordinator(
        hass, entry, _LOGGER, "Settings Data", timedelta(seconds=30), plenticore
    )

    entities = []
    for description in SELECT_SETTINGS_DATA:
        assert description.options is not None
        if description.module_id not in available_settings_data:
            continue
        needed_data_ids = {
            data_id for data_id in description.options if data_id != "None"
        }
        available_data_ids = {
            setting.id for setting in available_settings_data[description.module_id]
        }
        if not needed_data_ids <= available_data_ids:
            continue
        entities.append(
            PlenticoreDataSelect(
                select_data_update_coordinator,
                description,
                entry_id=entry.entry_id,
                platform_name=entry.title,
                device_info=plenticore.device_info,
            )
        )

    async_add_entities(entities)