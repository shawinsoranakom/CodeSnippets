async def async_setup_coordinated_entry(
    hass: HomeAssistant,
    config_entry: XiaomiMiioConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the coordinated switch from a config entry."""
    model = config_entry.data[CONF_MODEL]
    unique_id = config_entry.unique_id
    device = config_entry.runtime_data.device
    coordinator = config_entry.runtime_data.device_coordinator

    if DATA_KEY not in hass.data:
        hass.data[DATA_KEY] = {}

    device_features = 0

    if model in MODEL_TO_FEATURES_MAP:
        device_features = MODEL_TO_FEATURES_MAP[model]
    elif model in MODELS_HUMIDIFIER_MJJSQ:
        device_features = FEATURE_FLAGS_AIRHUMIDIFIER_MJSSQ
    elif model in MODELS_HUMIDIFIER:
        device_features = FEATURE_FLAGS_AIRHUMIDIFIER
    elif model in MODELS_PURIFIER_MIIO:
        device_features = FEATURE_FLAGS_AIRPURIFIER_MIIO
    elif model in MODELS_PURIFIER_MIOT:
        device_features = FEATURE_FLAGS_AIRPURIFIER_MIOT

    async_add_entities(
        XiaomiGenericCoordinatedSwitch(
            device,
            config_entry,
            f"{description.key}_{unique_id}",
            coordinator,
            description,
        )
        for description in SWITCH_TYPES
        if description.feature & device_features
    )