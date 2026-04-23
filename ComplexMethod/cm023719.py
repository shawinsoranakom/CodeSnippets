async def test_specificly_included_entity_always_wins_over_glob(
    hass: HomeAssistant,
) -> None:
    """Test specifically included entity always wins over a glob."""
    filter_accept = {
        "sensor.apc900va_status",
        "sensor.apc900va_battery_charge",
        "sensor.apc900va_battery_runtime",
        "sensor.apc900va_load",
        "sensor.energy_x",
    }
    filter_reject = {
        "sensor.apc900va_not_included",
    }
    conf = {
        CONF_EXCLUDE: {
            CONF_DOMAINS: [
                "updater",
                "camera",
                "group",
                "media_player",
                "script",
                "sun",
                "automation",
                "zone",
                "weblink",
                "scene",
                "calendar",
                "weather",
                "remote",
                "notify",
                "switch",
                "shell_command",
                "media_player",
            ],
            CONF_ENTITY_GLOBS: ["sensor.apc900va_*"],
        },
        CONF_INCLUDE: {
            CONF_DOMAINS: [
                "binary_sensor",
                "climate",
                "device_tracker",
                "input_boolean",
                "sensor",
            ],
            CONF_ENTITY_GLOBS: ["sensor.energy_*"],
            CONF_ENTITIES: [
                "sensor.apc900va_status",
                "sensor.apc900va_battery_charge",
                "sensor.apc900va_battery_runtime",
                "sensor.apc900va_load",
            ],
        },
    }
    extracted_filter = extract_include_exclude_filter_conf(conf)
    entity_filter = convert_include_exclude_filter(extracted_filter)
    sqlalchemy_filter = sqlalchemy_filter_from_include_exclude_conf(extracted_filter)
    assert sqlalchemy_filter is not None

    for entity_id in filter_accept:
        assert entity_filter(entity_id) is True

    for entity_id in filter_reject:
        assert entity_filter(entity_id) is False

    (
        filtered_states_entity_ids,
        filtered_events_entity_ids,
    ) = await _async_get_states_and_events_with_filter(
        hass, sqlalchemy_filter, filter_accept | filter_reject
    )

    assert filtered_states_entity_ids == filter_accept
    assert not filtered_states_entity_ids.intersection(filter_reject)

    assert filtered_events_entity_ids == filter_accept
    assert not filtered_events_entity_ids.intersection(filter_reject)