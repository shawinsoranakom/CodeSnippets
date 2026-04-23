def create_zha_config(hass: HomeAssistant, ha_zha_data: HAZHAData) -> ZHAData:
    """Create ZHA lib configuration from HA config objects."""

    # ensure that we have the necessary HA configuration data
    assert ha_zha_data.config_entry is not None
    assert ha_zha_data.yaml_config is not None

    # Remove brackets around IP addresses, this no longer works in CPython 3.11.4
    # This will be removed in 2023.11.0
    path = ha_zha_data.config_entry.data[CONF_DEVICE][CONF_DEVICE_PATH]
    cleaned_path = _clean_serial_port_path(path)

    if path != cleaned_path:
        _LOGGER.debug("Cleaned serial port path %r -> %r", path, cleaned_path)
        ha_zha_data.config_entry.data[CONF_DEVICE][CONF_DEVICE_PATH] = cleaned_path
        hass.config_entries.async_update_entry(
            ha_zha_data.config_entry, data=ha_zha_data.config_entry.data
        )

    # deep copy the yaml config to avoid modifying the original and to safely
    # pass it to the ZHA library
    app_config = copy.deepcopy(ha_zha_data.yaml_config.get(CONF_ZIGPY, {}))
    database = ha_zha_data.yaml_config.get(
        CONF_DATABASE,
        hass.config.path(DEFAULT_DATABASE_NAME),
    )
    app_config[CONF_DATABASE] = database
    app_config[CONF_DEVICE] = ha_zha_data.config_entry.data[CONF_DEVICE]

    radio_type = RadioType[ha_zha_data.config_entry.data[CONF_RADIO_TYPE]]

    # Until we have a way to coordinate channels with the Thread half of multi-PAN,
    # stick to the old zigpy default of channel 15 instead of dynamically scanning
    if (
        is_multiprotocol_url(app_config[CONF_DEVICE][CONF_DEVICE_PATH])
        and app_config.get(CONF_NWK, {}).get(CONF_NWK_CHANNEL) is None
    ):
        app_config.setdefault(CONF_NWK, {})[CONF_NWK_CHANNEL] = 15

    options: MappingProxyType[str, Any] = ha_zha_data.config_entry.options.get(
        CUSTOM_CONFIGURATION, {}
    )
    zha_options = CONF_ZHA_OPTIONS_SCHEMA(options.get(ZHA_OPTIONS, {}))
    ha_acp_options = CONF_ZHA_ALARM_SCHEMA(options.get(ZHA_ALARM_OPTIONS, {}))
    light_options: LightOptions = LightOptions(
        default_light_transition=zha_options.get(CONF_DEFAULT_LIGHT_TRANSITION),
        enable_enhanced_light_transition=zha_options.get(
            CONF_ENABLE_ENHANCED_LIGHT_TRANSITION
        ),
        enable_light_transitioning_flag=zha_options.get(
            CONF_ENABLE_LIGHT_TRANSITIONING_FLAG
        ),
        group_members_assume_state=zha_options.get(CONF_GROUP_MEMBERS_ASSUME_STATE),
    )
    device_options: DeviceOptions = DeviceOptions(
        enable_identify_on_join=zha_options.get(CONF_ENABLE_IDENTIFY_ON_JOIN),
        consider_unavailable_mains=zha_options.get(CONF_CONSIDER_UNAVAILABLE_MAINS),
        consider_unavailable_battery=zha_options.get(CONF_CONSIDER_UNAVAILABLE_BATTERY),
        enable_mains_startup_polling=zha_options.get(CONF_ENABLE_MAINS_STARTUP_POLLING),
    )
    acp_options: AlarmControlPanelOptions = AlarmControlPanelOptions(
        master_code=ha_acp_options.get(CONF_ALARM_MASTER_CODE),
        failed_tries=ha_acp_options.get(CONF_ALARM_FAILED_TRIES),
        arm_requires_code=ha_acp_options.get(CONF_ALARM_ARM_REQUIRES_CODE),
    )
    coord_config: CoordinatorConfiguration = CoordinatorConfiguration(
        path=app_config[CONF_DEVICE][CONF_DEVICE_PATH],
        baudrate=app_config[CONF_DEVICE][CONF_BAUDRATE],
        flow_control=app_config[CONF_DEVICE][CONF_FLOW_CONTROL],
        radio_type=radio_type.name,
    )
    quirks_config: QuirksConfiguration = QuirksConfiguration(
        enabled=ha_zha_data.yaml_config.get(CONF_ENABLE_QUIRKS, True),
        custom_quirks_path=ha_zha_data.yaml_config.get(CONF_CUSTOM_QUIRKS_PATH),
    )
    overrides_config: dict[str, DeviceOverridesConfiguration] = {}
    overrides: dict[str, dict[str, Any]] = cast(
        dict[str, dict[str, Any]], ha_zha_data.yaml_config.get(CONF_DEVICE_CONFIG)
    )
    if overrides is not None:
        for unique_id, override in overrides.items():
            overrides_config[unique_id] = DeviceOverridesConfiguration(
                type=override["type"],
            )

    return ZHAData(
        zigpy_config=app_config,
        config=ZHAConfiguration(
            light_options=light_options,
            device_options=device_options,
            alarm_control_panel_options=acp_options,
            coordinator_configuration=coord_config,
            quirks_configuration=quirks_config,
            device_overrides=overrides_config,
        ),
        local_timezone=ZoneInfo(hass.config.time_zone),
        country_code=hass.config.country,
    )