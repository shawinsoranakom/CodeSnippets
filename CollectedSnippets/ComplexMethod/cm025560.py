def _get_entities_for_appliance(
    appliance_coordinator: HomeConnectApplianceCoordinator,
) -> list[HomeConnectEntity]:
    """Get a list of entities."""
    return [
        *[
            HomeConnectEventSensor(appliance_coordinator, description)
            for description in EVENT_SENSORS
            if description.appliance_types
            and appliance_coordinator.data.info.type in description.appliance_types
        ],
        *[
            HomeConnectProgramSensor(appliance_coordinator, desc)
            for desc in BSH_PROGRAM_SENSORS
            if desc.appliance_types
            and appliance_coordinator.data.info.type in desc.appliance_types
        ],
        *[
            HomeConnectSensor(appliance_coordinator, description)
            for description in SENSORS
            if description.key in appliance_coordinator.data.status
        ],
    ]