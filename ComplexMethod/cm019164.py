async def test_options_functionality(
    hass: HomeAssistant,
    client: MagicMock,
    config_entry: MockConfigEntry,
    integration_setup: Callable[[MagicMock], Awaitable[bool]],
    entity_id: str,
    option_key: OptionKey,
    appliance: HomeAppliance,
    min: int,
    max: int,
    step_size: int,
    unit: str,
    set_active_program_options_side_effect: ActiveProgramNotSetError | None,
    set_selected_program_options_side_effect: SelectedProgramNotSetError | None,
    called_mock_method: str,
) -> None:
    """Test options functionality."""

    async def set_program_option_side_effect(ha_id: str, *_, **kwargs) -> None:
        event_key = EventKey(kwargs["option_key"])
        await client.add_events(
            [
                EventMessage(
                    ha_id,
                    EventType.NOTIFY,
                    ArrayOfEvents(
                        [
                            Event(
                                key=event_key,
                                raw_key=event_key.value,
                                timestamp=0,
                                level="",
                                handling="",
                                value=kwargs["value"],
                                unit=unit,
                            )
                        ]
                    ),
                ),
            ]
        )

    called_mock = AsyncMock(side_effect=set_program_option_side_effect)
    if set_active_program_options_side_effect:
        client.set_active_program_option.side_effect = (
            set_active_program_options_side_effect
        )
    else:
        assert set_selected_program_options_side_effect
        client.set_selected_program_option.side_effect = (
            set_selected_program_options_side_effect
        )
    setattr(client, called_mock_method, called_mock)
    client.get_available_program = AsyncMock(
        return_value=ProgramDefinition(
            ProgramKey.UNKNOWN,
            options=[
                ProgramDefinitionOption(
                    option_key,
                    "Double",
                    unit=unit,
                    constraints=ProgramDefinitionConstraints(
                        min=min,
                        max=max,
                        step_size=step_size,
                    ),
                )
            ],
        )
    )

    assert await integration_setup(client)
    assert config_entry.state is ConfigEntryState.LOADED
    entity_state = hass.states.get(entity_id)
    assert entity_state
    assert entity_state.attributes["unit_of_measurement"] == unit
    assert entity_state.attributes[ATTR_MIN] == min
    assert entity_state.attributes[ATTR_MAX] == max
    assert entity_state.attributes[ATTR_STEP] == step_size

    await hass.services.async_call(
        NUMBER_DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: entity_id, SERVICE_ATTR_VALUE: 80},
    )
    await hass.async_block_till_done()

    assert called_mock.called
    assert called_mock.call_args.args == (appliance.ha_id,)
    assert called_mock.call_args.kwargs == {
        "option_key": option_key,
        "value": 80,
    }
    assert hass.states.is_state(entity_id, "80.0")