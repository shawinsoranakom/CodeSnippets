async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up from config entry."""
    # Uses legacy hass.data[DOMAIN] pattern
    # pylint: disable-next=hass-use-runtime-data
    router = hass.data[DOMAIN].routers[config_entry.entry_id]
    sensors: list[Entity] = []
    for key in SENSOR_KEYS:
        if not (items := router.data.get(key)):
            continue
        if key_meta := SENSOR_META.get(key):
            if key_meta.include:
                items = {k: v for k, v in items.items() if key_meta.include.search(k)}
            if key_meta.exclude:
                items = {
                    k: v for k, v in items.items() if not key_meta.exclude.search(k)
                }
        for item, value in items.items():
            if value is None:
                _LOGGER.debug("Ignoring sensor %s.%s due to None value", key, item)
                continue
            if not (desc := SENSOR_META[key].descriptions.get(item)):
                _LOGGER.debug(  # pylint: disable=hass-logger-period # false positive
                    (
                        "Ignoring unknown sensor %s.%s. "
                        "Opening an issue at GitHub against the "
                        "huawei_lte integration would be appreciated, so we may be able to "
                        "add support for it in a future release. "
                        'Include the sensor name "%s.%s" in the issue, '
                        "as well as any information you may have about it, "
                        "such as values received for it as shown in the debug log."
                    ),
                    key,
                    item,
                    key,
                    item,
                )
                continue
            sensors.append(HuaweiLteSensor(router, key, item, desc))

    async_add_entities(sensors, True)