async def async_setup_entry(
    hass: HomeAssistant,
    entry: QnapQswConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add QNAP QSW binary sensors from a config_entry."""
    coordinator = entry.runtime_data.data_coordinator

    entities: list[QswBinarySensor] = [
        QswBinarySensor(coordinator, description, entry)
        for description in BINARY_SENSOR_TYPES
        if (
            description.key in coordinator.data
            and description.subkey in coordinator.data[description.key]
        )
    ]

    for description in LACP_PORT_BINARY_SENSOR_TYPES:
        if (
            description.key in coordinator.data
            and QSD_LACP_PORTS in coordinator.data[description.key]
        ):
            for port_id, port_values in coordinator.data[description.key][
                QSD_LACP_PORTS
            ].items():
                if description.subkey in port_values:
                    _desc = replace(
                        description,
                        sep_key=f"_lacp_port_{port_id}_",
                        name=f"LACP Port {port_id} {description.name}",
                    )
                    entities.append(QswBinarySensor(coordinator, _desc, entry, port_id))

    for description in PORT_BINARY_SENSOR_TYPES:
        if (
            description.key in coordinator.data
            and QSD_PORTS in coordinator.data[description.key]
        ):
            for port_id, port_values in coordinator.data[description.key][
                QSD_PORTS
            ].items():
                if description.subkey in port_values:
                    _desc = replace(
                        description,
                        sep_key=f"_port_{port_id}_",
                        name=f"Port {port_id} {description.name}",
                    )
                    entities.append(QswBinarySensor(coordinator, _desc, entry, port_id))

    async_add_entities(entities)