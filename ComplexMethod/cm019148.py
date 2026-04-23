async def test_select_functionality(
    hass: HomeAssistant,
    client: MagicMock,
    config_entry: MockConfigEntry,
    integration_setup: Callable[[MagicMock], Awaitable[bool]],
    appliance: HomeAppliance,
    entity_id: str,
    setting_key: SettingKey,
    expected_options: set[str],
    value_to_set: str,
    expected_value_call_arg: str,
) -> None:
    """Test select functionality."""
    assert await integration_setup(client)
    assert config_entry.state is ConfigEntryState.LOADED

    entity_state = hass.states.get(entity_id)
    assert entity_state
    assert set(entity_state.attributes[ATTR_OPTIONS]) == expected_options

    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {ATTR_ENTITY_ID: entity_id, ATTR_OPTION: value_to_set},
    )
    await hass.async_block_till_done()

    client.set_setting.assert_called_once()
    assert client.set_setting.call_args.args == (appliance.ha_id,)
    assert client.set_setting.call_args.kwargs == {
        "setting_key": setting_key,
        "value": expected_value_call_arg,
    }
    assert hass.states.is_state(entity_id, value_to_set)