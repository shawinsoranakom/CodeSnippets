async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Load a config entry."""
    # `_KNX_YAML_CONFIG` is only set in async_setup.
    # It's None when reloading the integration or no `knx` key in configuration.yaml
    config = hass.data.pop(_KNX_YAML_CONFIG, None)
    if config is None:
        _conf = await async_integration_yaml_config(hass, DOMAIN)
        if not _conf or DOMAIN not in _conf:
            # generate defaults
            config = CONFIG_SCHEMA({DOMAIN: {}})[DOMAIN]
        else:
            config = _conf[DOMAIN]
    try:
        knx_module = KNXModule(hass, config, entry)
        await knx_module.start()
    except XKNXException as ex:
        raise ConfigEntryNotReady from ex

    hass.data[KNX_MODULE_KEY] = knx_module

    knx_module.ui_time_server_controller.start(
        knx_module.xknx, knx_module.config_store.get_time_server_config()
    )
    knx_module.ui_expose_controller.start(
        hass, knx_module.xknx, knx_module.config_store.get_exposes()
    )
    if CONF_KNX_EXPOSE in config:
        knx_module.yaml_exposures.extend(
            create_combined_knx_exposure(hass, knx_module.xknx, config[CONF_KNX_EXPOSE])
        )

    configured_platforms_yaml = {
        platform for platform in SUPPORTED_PLATFORMS_YAML if platform in config
    }
    await hass.config_entries.async_forward_entry_setups(
        entry,
        {
            Platform.SENSOR,  # always forward sensor for system entities (telegram counter, etc.)
            *SUPPORTED_PLATFORMS_UI,  # forward all platforms that support UI entity management
            *configured_platforms_yaml,  # forward yaml-only managed platforms on demand,
        },
    )

    await register_panel(hass)

    return True