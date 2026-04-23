async def test_switch_state(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test the creation and values of the Modern Forms switches."""
    await init_integration(hass, aioclient_mock)

    state = hass.states.get("switch.modernformsfan_away_mode")
    assert state
    assert state.state == STATE_OFF

    entry = entity_registry.async_get("switch.modernformsfan_away_mode")
    assert entry
    assert entry.unique_id == "AA:BB:CC:DD:EE:FF_away_mode"

    state = hass.states.get("switch.modernformsfan_adaptive_learning")
    assert state
    assert state.state == STATE_OFF

    entry = entity_registry.async_get("switch.modernformsfan_adaptive_learning")
    assert entry
    assert entry.unique_id == "AA:BB:CC:DD:EE:FF_adaptive_learning"