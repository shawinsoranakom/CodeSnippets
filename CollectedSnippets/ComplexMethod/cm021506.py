async def test_trigger_entity_restore_state(
    hass: HomeAssistant,
    restored_state: str,
    initial_state: str,
    initial_attributes: list[str],
) -> None:
    """Test restoring trigger template binary sensor."""

    restored_attributes = {
        "entity_picture": "/local/cats.png",
        "icon": "mdi:ship",
        "plus_one": 55,
    }

    fake_state = State(
        TEST_BINARY_SENSOR.entity_id,
        restored_state,
        restored_attributes,
    )
    fake_extra_data = {
        "auto_off_time": None,
    }
    mock_restore_cache_with_extra_data(hass, ((fake_state, fake_extra_data),))
    await setup_entity(
        hass,
        TEST_BINARY_SENSOR,
        ConfigurationStyle.TRIGGER,
        1,
        {
            "device_class": "motion",
            "picture": "{{ '/local/dogs.png' }}",
            "icon": "{{ 'mdi:pirate' }}",
            "attributes": {
                "plus_one": "{{ trigger.event.data.beer + 1 }}",
                "another": "{{ trigger.event.data.uno_mas or 1 }}",
            },
        },
        _BEER_TRIGGER_VALUE_TEMPLATE,
    )

    state = hass.states.get(TEST_BINARY_SENSOR.entity_id)
    assert state.state == initial_state
    for attr, value in restored_attributes.items():
        if attr in initial_attributes:
            assert state.attributes[attr] == value
        else:
            assert attr not in state.attributes
    assert "another" not in state.attributes

    hass.bus.async_fire("test_event", {"beer": 2})
    await hass.async_block_till_done()

    state = hass.states.get(TEST_BINARY_SENSOR.entity_id)
    assert state.state == STATE_ON
    assert state.attributes["icon"] == "mdi:pirate"
    assert state.attributes["entity_picture"] == "/local/dogs.png"
    assert state.attributes["plus_one"] == 3
    assert state.attributes["another"] == 1