async def test_turn_on_off(
    hass: HomeAssistant,
    client: MagicMock,
    config_entry: MockConfigEntry,
    integration_setup: Callable[[MagicMock], Awaitable[bool]],
    appliance: HomeAppliance,
) -> None:
    """Test turning the climate entity on and off.

    The test also checks that the entity state is updated accordingly.
    """
    assert await integration_setup(client)
    assert config_entry.state is ConfigEntryState.LOADED

    entity_id = "climate.air_conditioner"

    state = hass.states.get(entity_id)
    assert state
    hvac_mode_state_while_turned_on = state.state
    assert hvac_mode_state_while_turned_on not in (HVACMode.OFF, STATE_UNKNOWN)

    for service, expected_setting_value, expected_state, call_count in (
        (SERVICE_TURN_OFF, BSH_POWER_STANDBY, HVACMode.OFF, 1),
        (SERVICE_TURN_ON, BSH_POWER_ON, hvac_mode_state_while_turned_on, 2),
    ):
        await hass.services.async_call(
            CLIMATE_DOMAIN, service, {"entity_id": entity_id}, True
        )
        await hass.async_block_till_done()

        client.set_setting.assert_awaited_with(
            appliance.ha_id,
            setting_key=SettingKey.BSH_COMMON_POWER_STATE,
            value=expected_setting_value,
        )
        assert client.set_setting.call_count == call_count
        assert hass.states.is_state(entity_id, expected_state)