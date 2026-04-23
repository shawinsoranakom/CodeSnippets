async def test_options_functionality(
    hass: HomeAssistant,
    client: MagicMock,
    config_entry: MockConfigEntry,
    integration_setup: Callable[[MagicMock], Awaitable[bool]],
    entity_id: str,
    option_key: OptionKey,
    allowed_values: list[str | None] | None,
    expected_options: set[str],
    appliance: HomeAppliance,
    set_active_program_options_side_effect: ActiveProgramNotSetError | None,
    set_selected_program_options_side_effect: SelectedProgramNotSetError | None,
    called_mock_method: str,
) -> None:
    """Test options functionality."""
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
            ProgramKey.UNKNOWN,
            options=[
                ProgramDefinitionOption(
                    option_key,
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
    assert set(entity_state.attributes[ATTR_OPTIONS]) == expected_options

    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {
            ATTR_ENTITY_ID: entity_id,
            ATTR_OPTION: "laundry_care_washer_enum_type_temperature_ul_warm",
        },
    )
    await hass.async_block_till_done()

    assert called_mock.called
    assert called_mock.call_args.args == (appliance.ha_id,)
    assert called_mock.call_args.kwargs == {
        "option_key": option_key,
        "value": "LaundryCare.Washer.EnumType.Temperature.UlWarm",
    }
    assert hass.states.is_state(
        entity_id, "laundry_care_washer_enum_type_temperature_ul_warm"
    )