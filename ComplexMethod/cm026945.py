def async_add_sensor(info: ZwaveDiscoveryInfo | NewZwaveDiscoveryInfo) -> None:
        """Add Z-Wave Sensor."""
        entities: list[ZWaveBaseEntity] = []

        if info.platform_data:
            data: NumericSensorDataTemplateData = info.platform_data
        else:
            data = NumericSensorDataTemplateData()

        entity_description = get_entity_description(data)

        if isinstance(info, NewZwaveDiscoveryInfo) and (
            entity_class := info.entity_class
        ) in (NewZWaveNumericSensor, NewZWaveMeterSensor):
            entities.append(entity_class(config_entry, driver, info))
        elif isinstance(info, NewZwaveDiscoveryInfo):
            pass  # other entity classes are not migrated yet
        elif info.platform_hint == "numeric_sensor":
            entities.append(
                ZWaveNumericSensor(
                    config_entry,
                    driver,
                    info,
                    entity_description,
                    data.unit_of_measurement,
                )
            )
        elif info.platform_hint == "notification":
            # prevent duplicate entities for values that are already represented as binary sensors
            if is_valid_notification_binary_sensor(info):
                return
            entities.append(
                ZWaveListSensor(config_entry, driver, info, entity_description)
            )
        elif info.platform_hint == "list":
            entities.append(
                ZWaveListSensor(config_entry, driver, info, entity_description)
            )
        elif info.platform_hint == "config_parameter":
            entities.append(
                ZWaveConfigParameterSensor(
                    config_entry, driver, info, entity_description
                )
            )
        elif info.platform_hint == "meter":
            entities.append(
                ZWaveMeterSensor(config_entry, driver, info, entity_description)
            )
        else:
            entities.append(ZwaveSensor(config_entry, driver, info, entity_description))

        async_add_entities(entities)