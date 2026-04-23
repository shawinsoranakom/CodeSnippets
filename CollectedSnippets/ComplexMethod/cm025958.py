async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Sensor set up for Hass.io config entry."""
    addons_coordinator = hass.data[ADDONS_COORDINATOR]
    coordinator = hass.data[MAIN_COORDINATOR]
    stats_coordinator = hass.data[STATS_COORDINATOR]

    entities: list[SensorEntity] = []

    # Add-on non-stats sensors (version, version_latest)
    entities.extend(
        HassioAddonSensor(
            addon=addon,
            coordinator=addons_coordinator,
            entity_description=entity_description,
        )
        for addon in addons_coordinator.data[DATA_KEY_ADDONS].values()
        for entity_description in COMMON_ENTITY_DESCRIPTIONS
    )

    # Add-on stats sensors (cpu_percent, memory_percent)
    entities.extend(
        HassioStatsSensor(
            coordinator=stats_coordinator,
            entity_description=entity_description,
            container_id=addon[ATTR_SLUG],
            data_key=DATA_KEY_ADDONS,
            device_id=addon[ATTR_SLUG],
            unique_id_prefix=addon[ATTR_SLUG],
        )
        for addon in addons_coordinator.data[DATA_KEY_ADDONS].values()
        for entity_description in STATS_ENTITY_DESCRIPTIONS
    )

    # Core stats sensors
    entities.extend(
        HassioStatsSensor(
            coordinator=stats_coordinator,
            entity_description=entity_description,
            container_id=CORE_CONTAINER,
            data_key=DATA_KEY_CORE,
            device_id="core",
            unique_id_prefix="home_assistant_core",
        )
        for entity_description in STATS_ENTITY_DESCRIPTIONS
    )

    # Supervisor stats sensors
    entities.extend(
        HassioStatsSensor(
            coordinator=stats_coordinator,
            entity_description=entity_description,
            container_id=SUPERVISOR_CONTAINER,
            data_key=DATA_KEY_SUPERVISOR,
            device_id="supervisor",
            unique_id_prefix="home_assistant_supervisor",
        )
        for entity_description in STATS_ENTITY_DESCRIPTIONS
    )

    # Host sensors
    entities.extend(
        HostSensor(
            coordinator=coordinator,
            entity_description=entity_description,
        )
        for entity_description in HOST_ENTITY_DESCRIPTIONS
    )

    # OS sensors
    if coordinator.is_hass_os:
        entities.extend(
            HassioOSSensor(
                coordinator=coordinator,
                entity_description=entity_description,
            )
            for entity_description in OS_ENTITY_DESCRIPTIONS
        )

    async_add_entities(entities)