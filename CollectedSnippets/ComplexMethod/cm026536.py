async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: VizioConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up a Vizio media player entry."""
    device_class = config_entry.data[CONF_DEVICE_CLASS]

    # If config entry options not set up, set them up,
    # otherwise assign values managed in options
    volume_step = config_entry.options.get(
        CONF_VOLUME_STEP, config_entry.data.get(CONF_VOLUME_STEP, DEFAULT_VOLUME_STEP)
    )

    params = {}
    if not config_entry.options:
        params["options"] = {CONF_VOLUME_STEP: volume_step}

        include_or_exclude_key = next(
            (
                key
                for key in config_entry.data.get(CONF_APPS, {})
                if key in (CONF_INCLUDE, CONF_EXCLUDE)
            ),
            None,
        )
        if include_or_exclude_key:
            params["options"][CONF_APPS] = {
                include_or_exclude_key: config_entry.data[CONF_APPS][
                    include_or_exclude_key
                ].copy()
            }

    if not config_entry.data.get(CONF_VOLUME_STEP):
        new_data = config_entry.data.copy()
        new_data.update({CONF_VOLUME_STEP: volume_step})
        params["data"] = new_data

    if params:
        hass.config_entries.async_update_entry(
            config_entry,
            **params,  # type: ignore[arg-type]
        )

    entity = VizioDevice(
        config_entry,
        device_class,
        config_entry.runtime_data.device_coordinator,
        hass.data.get(DATA_APPS) if device_class == MediaPlayerDeviceClass.TV else None,
    )

    async_add_entities([entity])