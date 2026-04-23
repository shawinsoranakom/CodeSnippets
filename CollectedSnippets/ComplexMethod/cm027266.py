async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: MyUplinkConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up myUplink sensor."""

    entities: list[SensorEntity] = []
    coordinator = config_entry.runtime_data

    # Setup device point sensors
    for device_id, point_data in coordinator.data.points.items():
        for point_id, device_point in point_data.items():
            if skip_entity(device_point.category, device_point):
                continue
            if find_matching_platform(device_point) == Platform.SENSOR:
                description = get_description(device_point)
                entity_class = MyUplinkDevicePointSensor
                # Ignore sensors without a description that provide non-numeric values
                if description is None and not isinstance(
                    device_point.value, (int, float)
                ):
                    continue
                if (
                    description is not None
                    and description.device_class == SensorDeviceClass.ENUM
                ):
                    entities.append(
                        MyUplinkEnumRawSensor(
                            coordinator=coordinator,
                            device_id=device_id,
                            device_point=device_point,
                            entity_description=description,
                            unique_id_suffix=f"{point_id}-raw",
                        )
                    )
                    entity_class = MyUplinkEnumSensor

                entities.append(
                    entity_class(
                        coordinator=coordinator,
                        device_id=device_id,
                        device_point=device_point,
                        entity_description=description,
                        unique_id_suffix=point_id,
                    )
                )

    async_add_entities(entities)