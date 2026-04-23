async def async_setup_entry(
    hass: HomeAssistant,
    entry: PlenticoreConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add kostal plenticore Switch."""
    plenticore = entry.runtime_data

    entities: list[Entity] = []

    available_settings_data = await plenticore.client.get_settings()
    settings_data_update_coordinator = SettingDataUpdateCoordinator(
        hass, entry, _LOGGER, "Settings Data", timedelta(seconds=30), plenticore
    )
    for description in SWITCH_SETTINGS_DATA:
        if (
            description.module_id not in available_settings_data
            or description.key
            not in (
                setting.id for setting in available_settings_data[description.module_id]
            )
        ):
            _LOGGER.debug(
                "Skipping non existing setting data %s/%s",
                description.module_id,
                description.key,
            )
            continue
        if entry.data.get(CONF_SERVICE_CODE) is None and description.installer_required:
            _LOGGER.debug(
                "Skipping installer required setting data %s/%s",
                description.module_id,
                description.key,
            )
            continue
        entities.append(
            PlenticoreDataSwitch(
                settings_data_update_coordinator,
                description,
                entry.entry_id,
                entry.title,
                plenticore.device_info,
            )
        )

    # add shadow management switches for strings which support it
    string_count_setting = await plenticore.client.get_setting_values(
        "devices:local", "Properties:StringCnt"
    )
    try:
        string_count = int(
            string_count_setting["devices:local"]["Properties:StringCnt"]
        )
    except ValueError:
        string_count = 0

    dc_strings = tuple(range(string_count))
    dc_string_feature_ids = tuple(
        PlenticoreShadowMgmtSwitch.DC_STRING_FEATURE_DATA_ID % dc_string
        for dc_string in dc_strings
    )

    dc_string_features = await plenticore.client.get_setting_values(
        PlenticoreShadowMgmtSwitch.MODULE_ID,
        dc_string_feature_ids,
    )

    for dc_string, dc_string_feature_id in zip(
        dc_strings, dc_string_feature_ids, strict=True
    ):
        try:
            dc_string_feature = int(
                dc_string_features[PlenticoreShadowMgmtSwitch.MODULE_ID][
                    dc_string_feature_id
                ]
            )
        except ValueError:
            dc_string_feature = 0

        if dc_string_feature == PlenticoreShadowMgmtSwitch.SHADOW_MANAGEMENT_SUPPORT:
            entities.append(
                PlenticoreShadowMgmtSwitch(
                    settings_data_update_coordinator,
                    dc_string,
                    entry.entry_id,
                    entry.title,
                    plenticore.device_info,
                )
            )
        else:
            _LOGGER.debug(
                "Skipping shadow management for DC string %d, not supported (Feature: %d)",
                dc_string + 1,
                dc_string_feature,
            )

    async_add_entities(entities)