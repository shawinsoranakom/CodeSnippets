async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: QnapConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up entry."""
    coordinator = config_entry.runtime_data
    uid = config_entry.unique_id
    assert uid is not None
    sensors: list[QNAPSensor] = []

    sensors.extend(
        [
            QNAPSystemSensor(coordinator, description, uid)
            for description in _SYSTEM_MON_COND
        ]
    )

    sensors.extend(
        [QNAPCPUSensor(coordinator, description, uid) for description in _CPU_MON_COND]
    )

    sensors.extend(
        [
            QNAPMemorySensor(coordinator, description, uid)
            for description in _MEMORY_MON_COND
        ]
    )

    # Network sensors
    sensors.extend(
        [
            QNAPNetworkSensor(coordinator, description, uid, nic)
            for nic in coordinator.data["system_stats"]["nics"]
            for description in _NETWORK_MON_COND
        ]
    )

    # Drive sensors
    sensors.extend(
        [
            QNAPDriveSensor(coordinator, description, uid, drive)
            for drive in coordinator.data["smart_drive_health"]
            for description in _DRIVE_MON_COND
        ]
    )

    # Volume sensors
    sensors.extend(
        [
            QNAPVolumeSensor(coordinator, description, uid, volume)
            for volume in coordinator.data["volumes"]
            for description in _VOLUME_MON_COND
        ]
    )
    async_add_entities(sensors)