async def test_switch_turn_on_off(
    hass: HomeAssistant,
    fc_class_mock,
    fh_class_mock,
    fs_class_mock,
    entity_id: str,
    wrapper_method: str,
    state_value: str,
) -> None:
    """Test Fritz!Tools switches turn on and turn off."""

    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_USER_DATA)
    entry.add_to_hass(hass)

    fc_class_mock.return_value = FritzConnectionMock(
        MOCK_FB_SERVICES | MOCK_CALL_DEFLECTION_DATA
    )

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert entry.state is ConfigEntryState.LOADED

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_ON

    with patch(
        f"homeassistant.components.fritz.coordinator.AvmWrapper.{wrapper_method}",
    ) as mock_set_action:
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        mock_set_action.assert_called_once()

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_OFF

    with patch(
        f"homeassistant.components.fritz.coordinator.AvmWrapper.{wrapper_method}",
    ) as mock_set_action_2:
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        mock_set_action_2.assert_called_once()

    assert (state := hass.states.get(entity_id))
    assert state.state == state_value