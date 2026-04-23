async def test_included_and_excluded_complex_case(hass: HomeAssistant) -> None:
    """Test filters with included and excluded with a complex filter."""
    filter_accept = {"light.any", "sensor.kitchen_4", "switch.kitchen"}
    filter_reject = {
        "camera.one",
        "notify.any",
        "automation.update_readme",
        "automation.update_utilities_cost",
        "binary_sensor.iss",
    }
    conf = {
        CONF_INCLUDE: {
            CONF_ENTITIES: ["group.trackers"],
        },
        CONF_EXCLUDE: {
            CONF_ENTITIES: [
                "automation.update_readme",
                "automation.update_utilities_cost",
                "binary_sensor.iss",
            ],
            CONF_DOMAINS: [
                "camera",
                "group",
                "media_player",
                "notify",
                "scene",
                "sun",
                "zone",
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