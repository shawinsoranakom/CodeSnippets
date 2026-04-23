async def test_included_and_excluded_simple_case_no_globs(hass: HomeAssistant) -> None:
    """Test filters with included and excluded without globs."""
    filter_accept = {"switch.bla", "sensor.blu", "sensor.keep"}
    filter_reject = {"sensor.bli"}
    conf = {
        CONF_INCLUDE: {
            CONF_DOMAINS: ["sensor", "homeassistant"],
            CONF_ENTITIES: ["switch.bla"],
        },
        CONF_EXCLUDE: {
            CONF_DOMAINS: ["switch"],
            CONF_ENTITIES: ["sensor.bli"],
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