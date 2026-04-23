async def async_setup_entry(
    hass: HomeAssistant,
    entry: AutomowerConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up number platform."""
    coordinator = entry.runtime_data
    entities: list[NumberEntity] = []
    for mower_id in coordinator.data:
        if coordinator.data[mower_id].capabilities.work_areas:
            _work_areas = coordinator.data[mower_id].work_areas
            if _work_areas is not None:
                entities.extend(
                    WorkAreaNumberEntity(
                        mower_id, coordinator, description, work_area_id
                    )
                    for description in WORK_AREA_NUMBER_TYPES
                    for work_area_id in _work_areas
                )
        entities.extend(
            AutomowerNumberEntity(mower_id, coordinator, description)
            for description in MOWER_NUMBER_TYPES
            if description.exists_fn(coordinator.data[mower_id])
        )
    async_add_entities(entities)

    def _async_add_new_work_areas(mower_id: str, work_area_ids: set[int]) -> None:
        async_add_entities(
            WorkAreaNumberEntity(mower_id, coordinator, description, work_area_id)
            for description in WORK_AREA_NUMBER_TYPES
            for work_area_id in work_area_ids
        )

    def _async_add_new_devices(mower_ids: set[str]) -> None:
        async_add_entities(
            AutomowerNumberEntity(mower_id, coordinator, description)
            for description in MOWER_NUMBER_TYPES
            for mower_id in mower_ids
            if description.exists_fn(coordinator.data[mower_id])
        )
        for mower_id in mower_ids:
            mower_data = coordinator.data[mower_id]
            if mower_data.capabilities.work_areas and mower_data.work_areas is not None:
                work_area_ids = set(mower_data.work_areas.keys())
                _async_add_new_work_areas(mower_id, work_area_ids)

    coordinator.new_areas_callbacks.append(_async_add_new_work_areas)
    coordinator.new_devices_callbacks.append(_async_add_new_devices)