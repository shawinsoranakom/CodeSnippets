async def test_speed_percentage_functionality(
    hass: HomeAssistant,
    client: MagicMock,
    config_entry: MockConfigEntry,
    integration_setup: Callable[[MagicMock], Awaitable[bool]],
    appliance: HomeAppliance,
    set_active_program_options_side_effect: ActiveProgramNotSetError | None,
    set_selected_program_options_side_effect: SelectedProgramNotSetError | None,
    called_mock_method: str,
) -> None:
    """Test speed percentage functionality."""
    entity_id = "fan.air_conditioner"
    option_key = OptionKey.HEATING_VENTILATION_AIR_CONDITIONING_AIR_CONDITIONER_FAN_SPEED_PERCENTAGE
    if set_active_program_options_side_effect:
        client.set_active_program_option.side_effect = (
            set_active_program_options_side_effect
        )
    else:
        assert set_selected_program_options_side_effect
        client.set_selected_program_option.side_effect = (
            set_selected_program_options_side_effect
        )
    called_mock: AsyncMock = getattr(client, called_mock_method)

    assert await integration_setup(client)
    assert config_entry.state is ConfigEntryState.LOADED
    assert not hass.states.is_state(entity_id, "50")

    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_SET_PERCENTAGE,
        {
            ATTR_ENTITY_ID: entity_id,
            ATTR_PERCENTAGE: 50,
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    called_mock.assert_called_once_with(
        appliance.ha_id,
        option_key=option_key,
        value=50,
    )
    entity_state = hass.states.get(entity_id)
    assert entity_state
    assert entity_state.attributes[ATTR_PERCENTAGE] == 50