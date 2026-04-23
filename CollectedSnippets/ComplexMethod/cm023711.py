async def test_included_and_excluded_simple_case_without_underscores(
    hass: HomeAssistant,
) -> None:
    """Test filters with included and excluded without underscores."""
    filter_accept = {"light.any", "sensor.kitchen4", "switch.kitchen"}
    filter_reject = {"switch.other", "cover.any", "sensor.weather5", "light.kitchen"}
    conf = {
        CONF_INCLUDE: {
            CONF_DOMAINS: ["light"],
            CONF_ENTITY_GLOBS: ["sensor.kitchen*"],
            CONF_ENTITIES: ["switch.kitchen"],
        },
        CONF_EXCLUDE: {
            CONF_DOMAINS: ["cover"],
            CONF_ENTITY_GLOBS: ["sensor.weather*"],
            CONF_ENTITIES: ["light.kitchen"],
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

    assert not entity_filter.explicitly_included("light.any")
    assert not entity_filter.explicitly_included("switch.other")
    assert entity_filter.explicitly_included("sensor.kitchen4")
    assert entity_filter.explicitly_included("switch.kitchen")

    assert not entity_filter.explicitly_excluded("light.any")
    assert not entity_filter.explicitly_excluded("switch.other")
    assert entity_filter.explicitly_excluded("sensor.weather5")
    assert entity_filter.explicitly_excluded("light.kitchen")

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