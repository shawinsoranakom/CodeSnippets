async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: WhirlpoolConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Config flow entry for Whirlpool sensors."""
    appliances_manager = config_entry.runtime_data

    washer_sensors = [
        WhirlpoolSensor(washer, description)
        for washer in appliances_manager.washers
        for description in WASHER_SENSORS
    ]

    washer_time_sensors = [
        WasherTimeSensor(washer, description)
        for washer in appliances_manager.washers
        for description in WASHER_DRYER_TIME_SENSORS
    ]

    dryer_sensors = [
        WhirlpoolSensor(dryer, description)
        for dryer in appliances_manager.dryers
        for description in DRYER_SENSORS
    ]

    dryer_time_sensors = [
        DryerTimeSensor(dryer, description)
        for dryer in appliances_manager.dryers
        for description in WASHER_DRYER_TIME_SENSORS
    ]

    oven_upper_cavity_sensors = [
        WhirlpoolOvenCavitySensor(oven, OvenCavity.Upper, description)
        for oven in appliances_manager.ovens
        if oven.get_oven_cavity_exists(OvenCavity.Upper)
        for description in OVEN_CAVITY_SENSORS
    ]

    oven_lower_cavity_sensors = [
        WhirlpoolOvenCavitySensor(oven, OvenCavity.Lower, description)
        for oven in appliances_manager.ovens
        if oven.get_oven_cavity_exists(OvenCavity.Lower)
        for description in OVEN_CAVITY_SENSORS
    ]

    async_add_entities(
        [
            *washer_sensors,
            *washer_time_sensors,
            *dryer_sensors,
            *dryer_time_sensors,
            *oven_upper_cavity_sensors,
            *oven_lower_cavity_sensors,
        ]
    )