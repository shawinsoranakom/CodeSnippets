def get_properties(device: Device, show_advanced=False):
    """Get the properties of an Insteon device and return the records and schema."""

    properties = []
    schema = {}

    for name, prop in device.configuration.items():
        if prop.is_read_only and not show_advanced:
            continue

        prop_schema = get_schema(prop, name, device.groups)
        if prop_schema is None:
            continue
        schema[name] = prop_schema
        properties.append(property_to_dict(prop))

    if show_advanced:
        for name, prop in device.operating_flags.items():
            if prop.property_type != PropertyType.ADVANCED:
                continue
            prop_schema = get_schema(prop, name, device.groups)
            if prop_schema is not None:
                schema[name] = prop_schema
                properties.append(property_to_dict(prop))
        for name, prop in device.properties.items():
            if prop.property_type != PropertyType.ADVANCED:
                continue
            prop_schema = get_schema(prop, name, device.groups)
            if prop_schema is not None:
                schema[name] = prop_schema
                properties.append(property_to_dict(prop))

    return properties, schema