async def test_same_entity_included_excluded_include_domain_wins(
    hass: HomeAssistant,
) -> None:
    """Test filters with domain and entities and the include domain wins."""
    filter_accept = {
        "media_player.test2",
        "media_player.test3",
        "thermostat.test",
    }
    filter_reject = {
        "thermostat.test2",
        "zone.home",
        "script.can_cancel_this_one",
    }
    conf = {
        CONF_INCLUDE: {
            CONF_DOMAINS: ["media_player"],
            CONF_ENTITIES: ["thermostat.test"],
        },
        CONF_EXCLUDE: {
            CONF_DOMAINS: ["thermostat"],
            CONF_ENTITIES: ["media_player.test"],
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