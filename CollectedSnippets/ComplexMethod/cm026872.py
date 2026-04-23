def _detect_device_type_and_class(
    node: Group | Node,
) -> tuple[BinarySensorDeviceClass | None, str | None]:
    try:
        device_type = node.type
    except AttributeError:
        # The type attribute didn't exist in the ISY's API response
        return (None, None)

    # Z-Wave Devices:
    if node.protocol == PROTO_ZWAVE:
        device_type = f"Z{node.zwave_props.category}"
        for device_class, values in BINARY_SENSOR_DEVICE_TYPES_ZWAVE.items():
            if node.zwave_props.category in values:
                return device_class, device_type
        return (None, device_type)

    # Other devices (incl Insteon.)
    for device_class, values in BINARY_SENSOR_DEVICE_TYPES_ISY.items():
        if any(device_type.startswith(t) for t in values):
            return device_class, device_type
    return (None, device_type)