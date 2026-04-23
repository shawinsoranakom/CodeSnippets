async def async_setup_entry(
    hass: HomeAssistant,
    entry: AutomowerConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up switch platform."""
    coordinator = entry.runtime_data
    entities: list[SwitchEntity] = []
    entities.extend(
        AutomowerScheduleSwitchEntity(mower_id, coordinator)
        for mower_id in coordinator.data
    )
    for mower_id in coordinator.data:
        if coordinator.data[mower_id].capabilities.stay_out_zones:
            _stay_out_zones = coordinator.data[mower_id].stay_out_zones
            if _stay_out_zones is not None:
                entities.extend(
                    StayOutZoneSwitchEntity(coordinator, mower_id, stay_out_zone_uid)
                    for stay_out_zone_uid in _stay_out_zones.zones
                )
        if coordinator.data[mower_id].capabilities.work_areas:
            _work_areas = coordinator.data[mower_id].work_areas
            if _work_areas is not None:
                entities.extend(
                    WorkAreaSwitchEntity(coordinator, mower_id, work_area_id)
                    for work_area_id in _work_areas
                )
    async_add_entities(entities)

    def _async_add_new_stay_out_zones(
        mower_id: str, stay_out_zone_uids: set[str]
    ) -> None:
        async_add_entities(
            StayOutZoneSwitchEntity(coordinator, mower_id, zone_uid)
            for zone_uid in stay_out_zone_uids
        )

    def _async_add_new_work_areas(mower_id: str, work_area_ids: set[int]) -> None:
        async_add_entities(
            WorkAreaSwitchEntity(coordinator, mower_id, work_area_id)
            for work_area_id in work_area_ids
        )

    def _async_add_new_devices(mower_ids: set[str]) -> None:
        async_add_entities(
            AutomowerScheduleSwitchEntity(mower_id, coordinator)
            for mower_id in mower_ids
        )
        for mower_id in mower_ids:
            mower_data = coordinator.data[mower_id]
            if (
                mower_data.capabilities.stay_out_zones
                and mower_data.stay_out_zones is not None
                and mower_data.stay_out_zones.zones is not None
            ):
                _async_add_new_stay_out_zones(
                    mower_id, set(mower_data.stay_out_zones.zones.keys())
                )
            if mower_data.capabilities.work_areas and mower_data.work_areas is not None:
                _async_add_new_work_areas(mower_id, set(mower_data.work_areas.keys()))

    coordinator.new_devices_callbacks.append(_async_add_new_devices)
    coordinator.new_zones_callbacks.append(_async_add_new_stay_out_zones)
    coordinator.new_areas_callbacks.append(_async_add_new_work_areas)