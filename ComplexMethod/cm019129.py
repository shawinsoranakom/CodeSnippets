async def test_fan_mode_functionality(
    hass: HomeAssistant,
    client: MagicMock,
    config_entry: MockConfigEntry,
    integration_setup: Callable[[MagicMock], Awaitable[bool]],
    allowed_values: list[str | None] | None,
    expected_fan_modes: list[str],
    appliance: HomeAppliance,
    set_active_program_options_side_effect: ActiveProgramNotSetError | None,
    set_selected_program_options_side_effect: SelectedProgramNotSetError | None,
    called_mock_method: str,
) -> None:
    """Test options functionality."""
    entity_id = "climate.air_conditioner"
    option_key = (
        OptionKey.HEATING_VENTILATION_AIR_CONDITIONING_AIR_CONDITIONER_FAN_SPEED_MODE
    )
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
    client.get_available_program = AsyncMock(
        return_value=ProgramDefinition(
            ProgramKey.HEATING_VENTILATION_AIR_CONDITIONING_AIR_CONDITIONER_AUTO,
            options=[
                ProgramDefinitionOption(
                    OptionKey.HEATING_VENTILATION_AIR_CONDITIONING_AIR_CONDITIONER_FAN_SPEED_MODE,
                    "Enumeration",
                    constraints=ProgramDefinitionConstraints(
                        allowed_values=allowed_values
                    ),
                )
            ],
        )
    )

    assert await integration_setup(client)
    assert config_entry.state is ConfigEntryState.LOADED
    entity_state = hass.states.get(entity_id)
    assert entity_state
    assert entity_state.attributes[ATTR_FAN_MODES] == expected_fan_modes

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_FAN_MODE,
        {
            ATTR_ENTITY_ID: entity_id,
            ATTR_FAN_MODE: expected_fan_modes[0],
        },
    )
    await hass.async_block_till_done()

    called_mock.assert_called_once_with(
        appliance.ha_id,
        option_key=option_key,
        value=allowed_values[0]
        if allowed_values
        else "HeatingVentilationAirConditioning.AirConditioner.EnumType.FanSpeedMode.Automatic",
    )
    entity_state = hass.states.get(entity_id)
    assert entity_state
    assert entity_state.attributes[ATTR_FAN_MODE] == expected_fan_modes[0]