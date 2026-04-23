async def test_trigger_entity_restore_state(
    hass: HomeAssistant,
    count: int,
    domain: str,
    config: dict,
) -> None:
    """Test restoring trigger event entities."""
    restored_attributes = {
        "entity_picture": "/local/cats.png",
        "event_type": "hold",
        "icon": "mdi:ship",
        "plus_one": 55,
    }
    fake_state = State(
        TEST_EVENT.entity_id,
        "2021-01-01T23:59:59.123+00:00",
        restored_attributes,
    )
    fake_extra_data = {
        "last_event_type": "hold",
        "last_event_attributes": restored_attributes,
    }
    mock_restore_cache_with_extra_data(hass, ((fake_state, fake_extra_data),))
    with assert_setup_component(count, domain):
        assert await async_setup_component(
            hass,
            domain,
            config,
        )

        await hass.async_block_till_done()
        await hass.async_start()
        await hass.async_block_till_done()

    test_state = "2021-01-01T23:59:59.123+00:00"
    state = hass.states.get(TEST_EVENT.entity_id)
    assert state.state == test_state
    for attr, value in restored_attributes.items():
        assert state.attributes[attr] == value
    assert "plus_two" not in state.attributes

    hass.bus.async_fire("test_event", {"action": "double", "beer": 2})
    await hass.async_block_till_done()

    state = hass.states.get(TEST_EVENT.entity_id)
    assert state.state != test_state
    assert state.attributes["icon"] == "mdi:pirate"
    assert state.attributes["entity_picture"] == "/local/dogs.png"
    assert state.attributes["event_type"] == "double"
    assert state.attributes["event_types"] == ["single", "double", "hold"]
    assert state.attributes["plus_one"] == 3
    assert state.attributes["plus_two"] == 4