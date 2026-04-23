async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: XiaomiMiioConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Selectors from a config entry."""
    entities = []
    if config_entry.data[CONF_FLOW_TYPE] != CONF_DEVICE:
        return
    model = config_entry.data[CONF_MODEL]
    device = config_entry.runtime_data.device
    coordinator = config_entry.runtime_data.device_coordinator

    if model in MODEL_TO_FEATURES_MAP:
        features = MODEL_TO_FEATURES_MAP[model]
    elif model in MODELS_PURIFIER_MIIO:
        features = FEATURE_FLAGS_AIRPURIFIER_MIIO
    elif model in MODELS_PURIFIER_MIOT:
        features = FEATURE_FLAGS_AIRPURIFIER_MIOT
    else:
        return

    for feature, description in NUMBER_TYPES.items():
        if feature == FEATURE_SET_LED_BRIGHTNESS and model != MODEL_FAN_ZA5:
            # Delete LED bightness entity created by mistake if it exists
            entity_reg = er.async_get(hass)
            entity_id = entity_reg.async_get_entity_id(
                PLATFORM_DOMAIN, DOMAIN, f"{description.key}_{config_entry.unique_id}"
            )
            if entity_id:
                entity_reg.async_remove(entity_id)
            continue
        if feature & features:
            if (
                description.key == ATTR_OSCILLATION_ANGLE
                and model in OSCILLATION_ANGLE_VALUES
            ):
                description = dataclasses.replace(
                    description,
                    native_max_value=OSCILLATION_ANGLE_VALUES[model].max_value,
                    native_min_value=OSCILLATION_ANGLE_VALUES[model].min_value,
                    native_step=OSCILLATION_ANGLE_VALUES[model].step,
                )
            elif description.key == ATTR_FAVORITE_LEVEL:
                for list_models, favorite_level_value in FAVORITE_LEVEL_VALUES.items():
                    if model in list_models:
                        description = dataclasses.replace(
                            description,
                            native_max_value=favorite_level_value.max_value,
                            native_min_value=favorite_level_value.min_value,
                            native_step=favorite_level_value.step,
                        )

            entities.append(
                XiaomiNumberEntity(
                    device,
                    config_entry,
                    f"{description.key}_{config_entry.unique_id}",
                    coordinator,
                    description,
                )
            )

    async_add_entities(entities)