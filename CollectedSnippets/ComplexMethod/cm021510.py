async def test_trigger_entity_restore_state(
    hass: HomeAssistant,
    count,
    domain,
    config,
    restored_state,
    restored_native_value,
    initial_state,
    initial_attributes,
) -> None:
    """Test restoring trigger template binary sensor."""

    restored_attributes = {
        "entity_picture": "/local/cats.png",
        "icon": "mdi:ship",
        "plus_one": 55,
    }

    fake_state = State(
        "sensor.test",
        restored_state,
        restored_attributes,
    )
    fake_extra_data = {
        "native_value": restored_native_value,
        "native_unit_of_measurement": None,
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

    state = hass.states.get("sensor.test")
    assert state.state == initial_state
    for attr, value in restored_attributes.items():
        if attr in initial_attributes:
            assert state.attributes[attr] == value
        else:
            assert attr not in state.attributes
    assert "another" not in state.attributes

    hass.bus.async_fire("test_event", {"beer": 2})
    await hass.async_block_till_done()

    state = hass.states.get("sensor.test")
    assert state.state == "2"
    assert state.attributes["icon"] == "mdi:pirate"
    assert state.attributes["entity_picture"] == "/local/dogs.png"
    assert state.attributes["plus_one"] == 3
    assert state.attributes["another"] == 1