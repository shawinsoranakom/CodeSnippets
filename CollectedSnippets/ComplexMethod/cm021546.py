async def test_non_optimistic_template_with_optimistic_state(
    hass: HomeAssistant, calls: list[ServiceCall]
) -> None:
    """Test optimistic state with non-optimistic template."""
    state = hass.states.get(TEST_COVER.entity_id)
    assert "entity_picture" not in state.attributes

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_SET_COVER_POSITION,
        {ATTR_ENTITY_ID: TEST_COVER.entity_id, ATTR_POSITION: 42},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get(TEST_COVER.entity_id)
    assert state.state == CoverState.OPEN
    assert state.attributes["current_position"] == 42.0
    assert "entity_picture" not in state.attributes

    await async_trigger(hass, TEST_STATE_ENTITY_ID, CoverState.OPEN)

    state = hass.states.get(TEST_COVER.entity_id)
    assert state.state == CoverState.OPEN
    assert state.attributes["current_position"] == 42.0
    assert state.attributes["entity_picture"] == "foo.png"