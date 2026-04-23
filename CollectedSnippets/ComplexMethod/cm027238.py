async def async_setup_entry(
    hass: HomeAssistant,
    entry: FitbitConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Fitbit sensor platform."""

    data = entry.runtime_data
    api = data.api

    # These are run serially to reuse the cached user profile, not gathered
    # to avoid two racing requests.
    user_profile = await api.async_get_user_profile()
    if user_profile.encoded_id is None:
        raise ConfigEntryNotReady("Could not get user profile")
    unit_system = await api.async_get_unit_system()

    fitbit_config = config_from_entry_data(entry.data)

    def is_explicit_enable(description: FitbitSensorEntityDescription) -> bool:
        """Determine if entity is enabled by default."""
        return fitbit_config.is_explicit_enable(description.key)

    def is_allowed_resource(description: FitbitSensorEntityDescription) -> bool:
        """Determine if an entity is allowed to be created."""
        return fitbit_config.is_allowed_resource(description.scope, description.key)

    resource_list = [
        *FITBIT_RESOURCES_LIST,
        SLEEP_START_TIME_12HR
        if fitbit_config.clock_format == "12H"
        else SLEEP_START_TIME,
    ]

    entities = [
        FitbitSensor(
            entry,
            api,
            user_profile.encoded_id,
            description,
            units=description.unit_fn(unit_system),
            enable_default_override=is_explicit_enable(description),
            device_info=_build_device_info(entry, description),
        )
        for description in resource_list
        if is_allowed_resource(description)
    ]
    async_add_entities(entities)

    if data.device_coordinator and is_allowed_resource(FITBIT_RESOURCE_BATTERY):
        battery_entities: list[SensorEntity] = [
            FitbitBatterySensor(
                data.device_coordinator,
                user_profile.encoded_id,
                FITBIT_RESOURCE_BATTERY,
                device=device,
                enable_default_override=is_explicit_enable(FITBIT_RESOURCE_BATTERY),
            )
            for device in data.device_coordinator.data.values()
        ]
        battery_entities.extend(
            FitbitBatteryLevelSensor(
                data.device_coordinator,
                user_profile.encoded_id,
                FITBIT_RESOURCE_BATTERY_LEVEL,
                device=device,
            )
            for device in data.device_coordinator.data.values()
        )
        async_add_entities(battery_entities)