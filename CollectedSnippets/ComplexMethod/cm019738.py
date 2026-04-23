async def test_cover_async_setup_entry(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_get: AsyncMock,
    mock_update: AsyncMock,
    snapshot: SnapshotAssertion,
) -> None:
    """Test switch platform."""

    await add_mock_config(hass)

    # Test Fresh Air Switch Entity
    entity_id = "switch.myzone_fresh_air"
    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_OFF

    entry = entity_registry.async_get(entity_id)
    assert entry
    assert entry.unique_id == "uniqueid-ac1-freshair"

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: [entity_id]},
        blocking=True,
    )
    mock_update.assert_called_once()
    mock_update.reset_mock()

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: [entity_id]},
        blocking=True,
    )
    mock_update.assert_called_once()
    mock_update.reset_mock()

    # Test MyFan Switch Entity
    entity_id = "switch.myzone_myfan"
    assert hass.states.get(entity_id) == snapshot(name=entity_id)

    entry = entity_registry.async_get(entity_id)
    assert entry
    assert entry.unique_id == "uniqueid-ac1-myfan"

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: [entity_id]},
        blocking=True,
    )
    mock_update.assert_called_once()
    assert mock_update.call_args[0][0] == snapshot(name=f"{entity_id}-turnon")
    mock_update.reset_mock()

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: [entity_id]},
        blocking=True,
    )
    mock_update.assert_called_once()
    assert mock_update.call_args[0][0] == snapshot(name=f"{entity_id}-turnoff")