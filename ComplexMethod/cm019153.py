async def test_light_functionality(
    hass: HomeAssistant,
    client: MagicMock,
    config_entry: MockConfigEntry,
    integration_setup: Callable[[MagicMock], Awaitable[bool]],
    entity_id: str,
    set_settings_args: dict[SettingKey, Any],
    service: str,
    exprected_attributes: dict[str, Any],
    state: str,
    appliance: HomeAppliance,
) -> None:
    """Test light functionality."""
    assert await integration_setup(client)
    assert config_entry.state is ConfigEntryState.LOADED

    service_data = exprected_attributes.copy()
    service_data[ATTR_ENTITY_ID] = entity_id
    await hass.services.async_call(
        LIGHT_DOMAIN,
        service,
        {key: value for key, value in service_data.items() if value is not None},
    )
    await hass.async_block_till_done()
    client.set_setting.assert_has_calls(
        [
            call(appliance.ha_id, setting_key=setting_key, value=value)
            for setting_key, value in set_settings_args.items()
        ]
    )
    entity_state = hass.states.get(entity_id)
    assert entity_state is not None
    assert entity_state.state == state
    for key, value in exprected_attributes.items():
        assert entity_state.attributes[key] == value