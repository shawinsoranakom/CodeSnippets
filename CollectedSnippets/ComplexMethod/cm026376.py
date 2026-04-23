async def async_service_temperature_set(
    entity: ClimateEntity, service_call: ServiceCall
) -> None:
    """Handle set temperature service."""
    if (
        ATTR_TEMPERATURE in service_call.data
        and not entity.supported_features & ClimateEntityFeature.TARGET_TEMPERATURE
    ):
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="missing_target_temperature_entity_feature",
        )
    if (
        ATTR_TARGET_TEMP_LOW in service_call.data
        and not entity.supported_features
        & ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
    ):
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="missing_target_temperature_range_entity_feature",
        )

    hass = entity.hass
    kwargs: dict[str, Any] = {}
    min_temp = entity.min_temp
    max_temp = entity.max_temp
    temp_unit = entity.temperature_unit

    if (
        (target_low_temp := service_call.data.get(ATTR_TARGET_TEMP_LOW))
        and (target_high_temp := service_call.data.get(ATTR_TARGET_TEMP_HIGH))
        and target_low_temp > target_high_temp
    ):
        # Ensure target_low_temp is not higher than target_high_temp.
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="low_temp_higher_than_high_temp",
        )

    for value, temp in service_call.data.items():
        if value in CONVERTIBLE_ATTRIBUTE:
            kwargs[value] = check_temp = TemperatureConverter.convert(
                temp, hass.config.units.temperature_unit, temp_unit
            )

            _LOGGER.debug(
                "Check valid temperature %d %s (%d %s) in range %d %s - %d %s",
                check_temp,
                entity.temperature_unit,
                temp,
                hass.config.units.temperature_unit,
                min_temp,
                temp_unit,
                max_temp,
                temp_unit,
            )
            if check_temp < min_temp or check_temp > max_temp:
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="temp_out_of_range",
                    translation_placeholders={
                        "check_temp": str(check_temp),
                        "min_temp": str(min_temp),
                        "max_temp": str(max_temp),
                    },
                )
        else:
            kwargs[value] = temp

    await entity.async_set_temperature(**kwargs)