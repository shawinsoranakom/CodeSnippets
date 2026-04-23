async def test_trigger_entity_restore_state(
    hass: HomeAssistant,
    count: int,
    domain: str,
    config: dict,
) -> None:
    """Test restoring trigger entities."""
    restored_attributes = {
        "installed_version": "1.0.0",
        "latest_version": "1.0.1",
        "entity_picture": "/local/cats.png",
        "icon": "mdi:ship",
        "skipped_version": "1.0.1",
    }
    fake_state = State(
        TEST_UPDATE.entity_id,
        STATE_OFF,
        restored_attributes,
    )
    mock_restore_cache_with_extra_data(hass, ((fake_state, {}),))
    with assert_setup_component(count, domain):
        assert await async_setup_component(
            hass,
            domain,
            config,
        )

        await hass.async_block_till_done()
        await hass.async_start()
        await hass.async_block_till_done()

    state = hass.states.get(TEST_UPDATE.entity_id)
    assert state.state == STATE_OFF
    for attr, value in restored_attributes.items():
        assert state.attributes[attr] == value

    hass.bus.async_fire("test_event", {"action": "1.0.0"})
    await hass.async_block_till_done()

    state = hass.states.get(TEST_UPDATE.entity_id)
    assert state.state == STATE_ON
    assert state.attributes["icon"] == "mdi:pirate"
    assert state.attributes["entity_picture"] == "/local/dogs.png"