def validate_binary_sensor_auto_off_has_trigger(obj: dict) -> dict:
    """Validate that binary sensors with auto_off have triggers."""
    if CONF_TRIGGERS not in obj and BINARY_SENSOR_DOMAIN in obj:
        binary_sensors: list[ConfigType] = obj[BINARY_SENSOR_DOMAIN]
        for binary_sensor in binary_sensors:
            if binary_sensor_platform.CONF_AUTO_OFF not in binary_sensor:
                continue

            identifier = f"{CONF_NAME}: {binary_sensor_platform.DEFAULT_NAME}"
            if (
                (name := binary_sensor.get(CONF_NAME))
                and isinstance(name, Template)
                and name.template != binary_sensor_platform.DEFAULT_NAME
            ):
                identifier = f"{CONF_NAME}: {name.template}"
            elif default_entity_id := binary_sensor.get(CONF_DEFAULT_ENTITY_ID):
                identifier = f"{CONF_DEFAULT_ENTITY_ID}: {default_entity_id}"
            elif unique_id := binary_sensor.get(CONF_UNIQUE_ID):
                identifier = f"{CONF_UNIQUE_ID}: {unique_id}"

            raise vol.Invalid(
                f"The auto_off option for template binary sensor: {identifier} "
                "requires a trigger, remove the auto_off option or rewrite "
                "configuration to use a trigger"
            )

    return obj