def _get_suggested_entities(hass: HomeAssistant) -> list[str]:
    """Return a sorted list of suggested sensor entity IDs for mapping."""
    ent_reg = er.async_get(hass)
    suitable_entities = []

    for entity_entry in ent_reg.entities.values():
        if not (
            entity_entry.domain == Platform.SENSOR and entity_entry.platform != DOMAIN
        ):
            continue

        if not hass.states.get(entity_entry.entity_id):
            continue

        state_class = (entity_entry.capabilities or {}).get("state_class")
        has_numeric_indicators = (
            state_class
            in (
                SensorStateClass.MEASUREMENT,
                SensorStateClass.TOTAL,
                SensorStateClass.TOTAL_INCREASING,
            )
            or entity_entry.device_class
            in (
                SensorDeviceClass.ENERGY,
                SensorDeviceClass.GAS,
                SensorDeviceClass.POWER,
                SensorDeviceClass.TEMPERATURE,
                SensorDeviceClass.VOLUME,
            )
            or entity_entry.original_device_class
            in (
                SensorDeviceClass.ENERGY,
                SensorDeviceClass.GAS,
                SensorDeviceClass.POWER,
                SensorDeviceClass.TEMPERATURE,
                SensorDeviceClass.VOLUME,
            )
        )

        if has_numeric_indicators:
            suitable_entities.append(entity_entry.entity_id)

    return sorted(suitable_entities)