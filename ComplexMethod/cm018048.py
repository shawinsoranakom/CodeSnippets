async def test_statemachine_remove(hass: HomeAssistant) -> None:
    """Test remove method."""
    hass.states.async_set("light.bowl", "on", {})
    events = async_capture_events(hass, EVENT_STATE_CHANGED)

    assert "light.bowl" in hass.states.async_entity_ids()
    assert hass.states.async_remove("light.bowl")
    await hass.async_block_till_done()

    assert "light.bowl" not in hass.states.async_entity_ids()
    assert len(events) == 1
    assert events[0].data.get("entity_id") == "light.bowl"
    assert events[0].data.get("old_state") is not None
    assert events[0].data["old_state"].entity_id == "light.bowl"
    assert events[0].data.get("new_state") is None

    # If it does not exist, we should get False
    assert not hass.states.async_remove("light.Bowl")
    await hass.async_block_till_done()
    assert len(events) == 1