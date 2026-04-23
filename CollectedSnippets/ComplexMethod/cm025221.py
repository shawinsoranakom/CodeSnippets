def _generate_schema(domain: str, flow_type: _FlowType) -> vol.Schema:
    """Generate schema."""
    schema: dict[vol.Marker, Any] = {}

    if flow_type == _FlowType.CONFIG:
        schema[vol.Required(CONF_NAME)] = TextSelector()

        if domain == Platform.BINARY_SENSOR:
            schema[vol.Optional(CONF_DEVICE_CLASS)] = SelectSelector(
                SelectSelectorConfig(
                    options=[cls.value for cls in BinarySensorDeviceClass],
                    sort=True,
                    mode=SelectSelectorMode.DROPDOWN,
                    translation_key="binary_sensor_device_class",
                ),
            )

    if domain == Platform.SENSOR:
        schema.update(
            {
                vol.Optional(CONF_MINIMUM, default=DEFAULT_MIN): cv.positive_int,
                vol.Optional(CONF_MAXIMUM, default=DEFAULT_MAX): cv.positive_int,
                vol.Optional(CONF_DEVICE_CLASS): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            cls.value
                            for cls in SensorDeviceClass
                            if cls != SensorDeviceClass.ENUM
                        ],
                        sort=True,
                        mode=SelectSelectorMode.DROPDOWN,
                        translation_key="sensor_device_class",
                    ),
                ),
                vol.Optional(CONF_UNIT_OF_MEASUREMENT): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            str(unit)
                            for units in DEVICE_CLASS_UNITS.values()
                            for unit in units
                            if unit is not None
                        ],
                        sort=True,
                        mode=SelectSelectorMode.DROPDOWN,
                        translation_key="sensor_unit_of_measurement",
                        custom_value=True,
                    ),
                ),
            }
        )

    return vol.Schema(schema)