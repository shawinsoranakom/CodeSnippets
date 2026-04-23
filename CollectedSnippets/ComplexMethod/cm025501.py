async def get_entities(
    onewire_hub: OneWireHub,
    devices: list[OWDeviceDescription],
    options: Mapping[str, Any],
) -> list[OneWireSensorEntity]:
    """Get a list of entities."""
    entities: list[OneWireSensorEntity] = []
    for device in devices:
        family = device.family
        device_type = device.type
        device_id = device.id
        device_info = device.device_info
        device_sub_type = "std"
        device_path = device.path
        if device_type and "EF" in family:
            device_sub_type = "HobbyBoard"
            family = device_type
        elif device_type and "7E" in family:
            device_sub_type = "EDS"
            family = device_type
        elif "A6" in family:
            # A6 is a secondary family code for DS2438
            family = "26"

        if family not in get_sensor_types(device_sub_type):
            continue
        for description in get_sensor_types(device_sub_type)[family]:
            if description.key.startswith("moisture/"):
                s_id = description.key.split(".")[1]
                is_leaf = int(
                    (
                        await onewire_hub.owproxy.read(
                            f"{device_path}moisture/is_leaf.{s_id}"
                        )
                    ).decode()
                )
                if is_leaf:
                    description = dataclasses.replace(
                        description,
                        device_class=SensorDeviceClass.HUMIDITY,
                        native_unit_of_measurement=PERCENTAGE,
                        translation_key="wetness_id",
                        translation_placeholders={"id": s_id},
                    )
            override_key = None
            if description.override_key:
                override_key = description.override_key(device_id, options)
            device_file = os.path.join(
                os.path.split(device.path)[0],
                override_key or description.key,
            )
            if family == "12":
                # We need to check if there is TAI8570 plugged in
                try:
                    await onewire_hub.owproxy.read(device_file)
                except OWServerReturnError as err:
                    _LOGGER.debug(
                        "Ignoring unreachable sensor %s",
                        device_file,
                        exc_info=err,
                    )
                    continue
            entities.append(
                OneWireSensorEntity(
                    description=description,
                    device_id=device_id,
                    device_file=device_file,
                    device_info=device_info,
                    owproxy=onewire_hub.owproxy,
                )
            )
    return entities