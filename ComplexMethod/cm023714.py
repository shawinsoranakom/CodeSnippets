async def test_included_entities_and_excluded_domain(hass: HomeAssistant) -> None:
    """Test filters with included entities and excluded domain."""
    filter_accept = {
        "media_player.test",
        "media_player.test3",
        "thermostat.test",
        "zone.home",
        "script.can_cancel_this_one",
    }
    filter_reject = {
        "thermostat.test2",
    }
    conf = {
        CONF_INCLUDE: {
            CONF_ENTITIES: ["media_player.test", "thermostat.test"],
        },
        CONF_EXCLUDE: {
            CONF_DOMAINS: ["thermostat"],
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