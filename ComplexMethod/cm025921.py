def _build_entities(
    device_list: list[ViCareDevice],
) -> list[ViCareBinarySensor]:
    """Create ViCare binary sensor entities for a device."""

    entities: list[ViCareBinarySensor] = []
    for device in device_list:
        # add device entities
        entities.extend(
            ViCareBinarySensor(
                description,
                get_device_serial(device.api),
                device.config,
                device.api,
            )
            for description in GLOBAL_SENSORS
            if is_supported(description.key, description.value_getter, device.api)
        )
        # add component entities
        for component_list, entity_description_list in (
            (get_circuits(device.api), CIRCUIT_SENSORS),
            (get_burners(device.api), BURNER_SENSORS),
            (get_compressors(device.api), COMPRESSOR_SENSORS),
        ):
            entities.extend(
                ViCareBinarySensor(
                    description,
                    get_device_serial(device.api),
                    device.config,
                    device.api,
                    component,
                )
                for component in component_list
                for description in entity_description_list
                if is_supported(description.key, description.value_getter, component)
            )
    return entities