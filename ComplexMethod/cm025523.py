async def async_setup_entry(
    hass: HomeAssistant,
    entry: DevoloHomeNetworkConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Get all devices and sensors and setup them via config entry."""
    device = entry.runtime_data.device
    coordinators = entry.runtime_data.coordinators

    entities: list[BaseDevoloSensorEntity[Any, Any, Any]] = []
    if device.plcnet:
        entities.append(
            DevoloSensorEntity(
                entry,
                coordinators[CONNECTED_PLC_DEVICES],
                SENSOR_TYPES[CONNECTED_PLC_DEVICES],
            )
        )
        network: LogicalNetwork = coordinators[CONNECTED_PLC_DEVICES].data
        peers = [
            peer.mac_address for peer in network.devices if peer.topology == REMOTE
        ]
        for peer in peers:
            entities.append(
                DevoloPlcDataRateSensorEntity(
                    entry,
                    coordinators[CONNECTED_PLC_DEVICES],
                    SENSOR_TYPES[PLC_TX_RATE],
                    peer,
                )
            )
            entities.append(
                DevoloPlcDataRateSensorEntity(
                    entry,
                    coordinators[CONNECTED_PLC_DEVICES],
                    SENSOR_TYPES[PLC_RX_RATE],
                    peer,
                )
            )
    if device.device and "restart" in device.device.features:
        entities.append(
            DevoloSensorEntity(
                entry,
                coordinators[LAST_RESTART],
                SENSOR_TYPES[LAST_RESTART],
            )
        )
    if device.device and "wifi1" in device.device.features:
        entities.append(
            DevoloSensorEntity(
                entry,
                coordinators[CONNECTED_WIFI_CLIENTS],
                SENSOR_TYPES[CONNECTED_WIFI_CLIENTS],
            )
        )
        entities.append(
            DevoloSensorEntity(
                entry,
                coordinators[NEIGHBORING_WIFI_NETWORKS],
                SENSOR_TYPES[NEIGHBORING_WIFI_NETWORKS],
            )
        )
    async_add_entities(entities)