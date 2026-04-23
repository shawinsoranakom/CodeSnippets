async def test_switches(
    hass: HomeAssistant,
    entity: str,
    mock_config_entry: MockConfigEntry,
    mock_smlight_client: MagicMock,
    setting: Settings,
) -> None:
    """Test the SMLIGHT switches."""
    await setup_integration(hass, mock_config_entry)

    _page, _toggle = setting.value

    entity_id = f"switch.mock_title_{entity}"
    state = hass.states.get(entity_id)
    assert state is not None

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    assert len(mock_smlight_client.set_toggle.mock_calls) == 1
    mock_smlight_client.set_toggle.assert_called_once_with(_page, _toggle, True)

    event_function: Callable[[SettingsEvent], None] = next(
        (
            call_args[0][1]
            for call_args in mock_smlight_client.sse.register_settings_cb.call_args_list
            if setting == call_args[0][0]
        ),
        None,
    )

    async def _call_event_function(state: bool = True):
        event_function(SettingsEvent(page=_page, origin="ha", setting={_toggle: state}))
        await hass.async_block_till_done()

    await _call_event_function(state=True)

    state = hass.states.get(entity_id)
    assert state.state == STATE_ON

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    assert len(mock_smlight_client.set_toggle.mock_calls) == 2
    mock_smlight_client.set_toggle.assert_called_with(_page, _toggle, False)

    await _call_event_function(state=False)

    state = hass.states.get(entity_id)
    assert state.state == STATE_OFF