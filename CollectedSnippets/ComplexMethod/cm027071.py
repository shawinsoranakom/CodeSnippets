async def async_setup_entry(
    hass: HomeAssistant,
    entry: AutomowerConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up sensor platform."""
    coordinator = entry.runtime_data
    entities: list[SensorEntity] = []
    for mower_id in coordinator.data:
        if coordinator.data[mower_id].capabilities.work_areas:
            _work_areas = coordinator.data[mower_id].work_areas
            if _work_areas is not None:
                entities.extend(
                    WorkAreaSensorEntity(
                        mower_id, coordinator, description, work_area_id
                    )
                    for description in WORK_AREA_SENSOR_TYPES
                    for work_area_id in _work_areas
                    if description.exists_fn(_work_areas[work_area_id])
                )
        entities.extend(
            AutomowerSensorEntity(mower_id, coordinator, description)
            for description in MOWER_SENSOR_TYPES
            if description.exists_fn(coordinator.data[mower_id])
        )
    async_add_entities(entities)

    def _async_add_new_work_areas(mower_id: str, work_area_ids: set[int]) -> None:
        mower_data = coordinator.data[mower_id]
        if mower_data.work_areas is None:
            return

        async_add_entities(
            WorkAreaSensorEntity(mower_id, coordinator, description, work_area_id)
            for description in WORK_AREA_SENSOR_TYPES
            for work_area_id in work_area_ids
            if work_area_id in mower_data.work_areas
            and description.exists_fn(mower_data.work_areas[work_area_id])
        )

    def _async_add_new_devices(mower_ids: set[str]) -> None:
        async_add_entities(
            AutomowerSensorEntity(mower_id, coordinator, description)
            for mower_id in mower_ids
            for description in MOWER_SENSOR_TYPES
            if description.exists_fn(coordinator.data[mower_id])
        )
        for mower_id in mower_ids:
            mower_data = coordinator.data[mower_id]
            if mower_data.capabilities.work_areas and mower_data.work_areas is not None:
                _async_add_new_work_areas(
                    mower_id,
                    set(mower_data.work_areas.keys()),
                )

    coordinator.new_devices_callbacks.append(_async_add_new_devices)
    coordinator.new_areas_callbacks.append(_async_add_new_work_areas)