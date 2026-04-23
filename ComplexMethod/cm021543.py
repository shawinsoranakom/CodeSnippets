async def test_optimistic_in_progress_with_update_percent_template(
    hass: HomeAssistant,
) -> None:
    """Test optimistic in_progress attribute with update percent templates."""
    # Ensure trigger entities trigger.
    state = hass.states.get(TEST_UPDATE.entity_id)
    assert state.attributes["in_progress"] is False
    assert state.attributes["update_percentage"] is None

    for i in range(101):
        state = hass.states.async_set(TEST_SENSOR_ID, i)
        await hass.async_block_till_done()

        state = hass.states.get(TEST_UPDATE.entity_id)
        assert state.attributes["in_progress"] is True
        assert state.attributes["update_percentage"] == i

    state = hass.states.async_set(TEST_SENSOR_ID, STATE_UNAVAILABLE)
    await hass.async_block_till_done()

    state = hass.states.get(TEST_UPDATE.entity_id)
    assert state.attributes["in_progress"] is False
    assert state.attributes["update_percentage"] is None