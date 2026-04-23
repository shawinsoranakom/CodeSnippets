async def async_setup_entry(
    hass: HomeAssistant,
    entry: EzvizConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up EZVIZ select entities based on a config entry."""
    coordinator = entry.runtime_data

    entities = [
        EzvizSelect(coordinator, camera, ALARM_SOUND_MODE_SELECT_TYPE)
        for camera in coordinator.data
        for switch in coordinator.data[camera]["switches"]
        if switch == ALARM_SOUND_MODE_SELECT_TYPE.supported_switch
    ]

    for camera in coordinator.data:
        device_category = coordinator.data[camera].get("device_category")
        supportExt = coordinator.data[camera].get("supportExt")
        if (
            device_category == DeviceCatagories.BATTERY_CAMERA_DEVICE_CATEGORY.value
            and supportExt
            and str(SupportExt.SupportBatteryManage.value) in supportExt
        ):
            entities.append(
                EzvizSelect(coordinator, camera, BATTERY_WORK_MODE_SELECT_TYPE)
            )

    async_add_entities(entities)