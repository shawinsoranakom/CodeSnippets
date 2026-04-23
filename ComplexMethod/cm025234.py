async def async_create_miio_device_and_coordinator(
    hass: HomeAssistant, entry: XiaomiMiioConfigEntry
) -> None:
    """Set up a data coordinator and one miio device to service multiple entities."""
    model: str = entry.data[CONF_MODEL]
    host = entry.data[CONF_HOST]
    token = entry.data[CONF_TOKEN]
    name = entry.title
    migrate = False
    update_method = _async_update_data_default
    coordinator_class: type[DataUpdateCoordinator[Any]] = DataUpdateCoordinator

    # List of models requiring specific lazy_discover setting
    LAZY_DISCOVER_FOR_MODEL = {
        "zhimi.fan.za3": True,
        "zhimi.fan.za5": True,
        "zhimi.airpurifier.za1": True,
        "dmaker.fan.1c": True,
    }
    lazy_discover = LAZY_DISCOVER_FOR_MODEL.get(model, False)

    if (
        model not in MODELS_HUMIDIFIER
        and model not in MODELS_FAN
        and model not in MODELS_VACUUM
        and not model.startswith(ROBOROCK_GENERIC)
        and not model.startswith(ROCKROBO_GENERIC)
    ):
        return

    _LOGGER.debug("Initializing with host %s (token %s...)", host, token[:5])

    device: MiioDevice
    # Humidifiers
    if model in MODELS_HUMIDIFIER_MIOT:
        device = AirHumidifierMiot(host, token, lazy_discover=lazy_discover)
        migrate = True
    elif model in MODELS_HUMIDIFIER_MJJSQ:
        device = AirHumidifierMjjsq(
            host, token, lazy_discover=lazy_discover, model=model
        )
        migrate = True
    elif model in MODELS_HUMIDIFIER_MIIO:
        device = AirHumidifier(host, token, lazy_discover=lazy_discover, model=model)
        migrate = True
    # Airpurifiers and Airfresh
    elif model in MODELS_PURIFIER_MIOT:
        device = AirPurifierMiot(host, token, lazy_discover=lazy_discover)
    elif model.startswith("zhimi.airpurifier."):
        device = AirPurifier(host, token, lazy_discover=lazy_discover)
    elif model.startswith("zhimi.airfresh."):
        device = AirFresh(host, token, lazy_discover=lazy_discover)
    elif model == MODEL_AIRFRESH_A1:
        device = AirFreshA1(host, token, lazy_discover=lazy_discover)
    elif model == MODEL_AIRFRESH_T2017:
        device = AirFreshT2017(host, token, lazy_discover=lazy_discover)
    elif model in MODELS_VACUUM or model.startswith(
        (ROBOROCK_GENERIC, ROCKROBO_GENERIC)
    ):
        # TODO: add lazy_discover as argument when python-miio add support # pylint: disable=fixme
        device = RoborockVacuum(host, token)
        update_method = _async_update_data_vacuum
        coordinator_class = DataUpdateCoordinator[VacuumCoordinatorData]
    # Pedestal fans
    elif model in MODEL_TO_CLASS_MAP:
        device = MODEL_TO_CLASS_MAP[model](host, token, lazy_discover=lazy_discover)
    elif model in MODELS_FAN_MIIO:
        device = Fan(host, token, lazy_discover=lazy_discover, model=model)
    else:
        _LOGGER.error(
            (
                "Unsupported device found! Please create an issue at "
                "https://github.com/syssi/xiaomi_airpurifier/issues "
                "and provide the following data: %s"
            ),
            model,
        )
        return

    if migrate:
        # Removing fan platform entity for humidifiers and migrate the name
        # to the config entry for migration
        entity_registry = er.async_get(hass)
        assert entry.unique_id
        entity_id = entity_registry.async_get_entity_id("fan", DOMAIN, entry.unique_id)
        if entity_id:
            # This check is entities that have a platform migration only
            # and should be removed in the future
            if (entity := entity_registry.async_get(entity_id)) and (
                migrate_entity_name := entity.name
            ):
                hass.config_entries.async_update_entry(entry, title=migrate_entity_name)
            entity_registry.async_remove(entity_id)

    # Create update miio device and coordinator
    coordinator = coordinator_class(
        hass,
        _LOGGER,
        config_entry=entry,
        name=name,
        update_method=update_method(hass, device),
        # Polling interval. Will only be polled if there are subscribers.
        update_interval=UPDATE_INTERVAL,
    )

    # Trigger first data fetch
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = XiaomiMiioRuntimeData(
        device=device, device_coordinator=coordinator
    )