async def async_setup_entry(
    hass: HomeAssistant,
    entry: AzureDevOpsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Azure DevOps sensor based on a config entry."""
    coordinator = entry.runtime_data
    initial_builds: list[Build] = coordinator.data.builds

    entities: list[SensorEntity] = [
        AzureDevOpsBuildSensor(
            coordinator,
            description,
            key,
        )
        for description in BASE_BUILD_SENSOR_DESCRIPTIONS
        for key, build in enumerate(initial_builds)
        if build.project and build.definition
    ]

    entities.extend(
        AzureDevOpsWorkItemSensor(
            coordinator,
            description,
            key,
            state_key,
        )
        for description in BASE_WORK_ITEM_SENSOR_DESCRIPTIONS
        for key, work_item_type_state in enumerate(coordinator.data.work_items)
        for state_key, _ in enumerate(work_item_type_state.state_items)
    )

    async_add_entities(entities)