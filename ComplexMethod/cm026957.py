def get_value_state_schema(
    value: ZwaveValue,
) -> VolSchemaType | vol.Coerce | vol.In | None:
    """Return device automation schema for a config entry."""
    if isinstance(value, ConfigurationValue):
        min_ = value.metadata.min
        max_ = value.metadata.max
        if value.configuration_value_type in (
            ConfigurationValueType.RANGE,
            ConfigurationValueType.MANUAL_ENTRY,
        ):
            return vol.All(vol.Coerce(int), vol.Range(min=min_, max=max_))

        if value.configuration_value_type == ConfigurationValueType.BOOLEAN:
            return vol.Coerce(bool)

        if value.configuration_value_type == ConfigurationValueType.ENUMERATED:
            return vol.In({str(int(k)): v for k, v in value.metadata.states.items()})

        return None

    if value.metadata.states:
        return vol.In({str(int(k)): v for k, v in value.metadata.states.items()})

    return vol.All(
        vol.Coerce(int),
        vol.Range(min=value.metadata.min, max=value.metadata.max),
    )