async def test_installed_and_latest_template_updates_from_entity(
    hass: HomeAssistant,
) -> None:
    """Test template installed and latest version templates updates from entities."""
    hass.states.async_set(TEST_INSTALLED_SENSOR, "1.0")
    hass.states.async_set(TEST_LATEST_SENSOR, "2.0")
    await hass.async_block_till_done()

    state = hass.states.get(TEST_UPDATE.entity_id)
    assert state is not None
    assert state.state == STATE_ON
    assert state.attributes["installed_version"] == "1.0"
    assert state.attributes["latest_version"] == "2.0"

    hass.states.async_set(TEST_INSTALLED_SENSOR, "2.0")
    hass.states.async_set(TEST_LATEST_SENSOR, "2.0")
    await hass.async_block_till_done()

    state = hass.states.get(TEST_UPDATE.entity_id)
    assert state is not None
    assert state.state == STATE_OFF
    assert state.attributes["installed_version"] == "2.0"
    assert state.attributes["latest_version"] == "2.0"

    hass.states.async_set(TEST_INSTALLED_SENSOR, "2.0")
    hass.states.async_set(TEST_LATEST_SENSOR, "3.0")
    await hass.async_block_till_done()

    state = hass.states.get(TEST_UPDATE.entity_id)
    assert state is not None
    assert state.state == STATE_ON
    assert state.attributes["installed_version"] == "2.0"
    assert state.attributes["latest_version"] == "3.0"