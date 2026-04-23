async def test_program_options_retrieval(
    hass: HomeAssistant,
    client: MagicMock,
    config_entry: MockConfigEntry,
    integration_setup: Callable[[MagicMock], Awaitable[bool]],
    array_of_programs_program_arg: str,
    event_key: EventKey,
    appliance: HomeAppliance,
    option_entity_id: dict[OptionKey, str],
    options_state_stage_1: list[tuple[str, bool | None]],
    options_availability_stage_2: list[bool],
    option_without_default: tuple[OptionKey, str],
    option_without_constraints: tuple[OptionKey, str],
) -> None:
    """Test that the options are correctly retrieved at the start and updated on program updates."""
    original_get_all_programs_mock = client.get_all_programs.side_effect
    options_values = [
        Option(
            option_key,
            value,
        )
        for option_key, (_, value) in zip(
            option_entity_id.keys(), options_state_stage_1, strict=True
        )
        if value is not None
    ]

    async def get_all_programs_with_options_mock(ha_id: str) -> ArrayOfPrograms:
        if ha_id != appliance.ha_id:
            return await original_get_all_programs_mock(ha_id)

        array_of_programs: ArrayOfPrograms = await original_get_all_programs_mock(ha_id)
        return ArrayOfPrograms(
            **(
                {
                    "programs": array_of_programs.programs,
                    array_of_programs_program_arg: Program(
                        array_of_programs.programs[0].key, options=options_values
                    ),
                }
            )
        )

    client.get_all_programs = AsyncMock(side_effect=get_all_programs_with_options_mock)
    client.get_available_program = AsyncMock(
        return_value=ProgramDefinition(
            ProgramKey.UNKNOWN,
            options=[
                ProgramDefinitionOption(
                    option_key,
                    "Boolean",
                    constraints=ProgramDefinitionConstraints(
                        default=False,
                    ),
                )
                for option_key, (_, value) in zip(
                    option_entity_id.keys(), options_state_stage_1, strict=True
                )
                if value is not None
            ],
        )
    )

    assert await integration_setup(client)
    assert config_entry.state is ConfigEntryState.LOADED

    for entity_id, (state, _) in zip(
        option_entity_id.values(), options_state_stage_1, strict=True
    ):
        if state is not None:
            assert hass.states.is_state(entity_id, state)
        else:
            assert not hass.states.get(entity_id)

    client.get_available_program = AsyncMock(
        return_value=ProgramDefinition(
            ProgramKey.UNKNOWN,
            options=[
                *[
                    ProgramDefinitionOption(
                        option_key,
                        "Boolean",
                        constraints=ProgramDefinitionConstraints(
                            default=False,
                        ),
                    )
                    for option_key, available in zip(
                        option_entity_id.keys(),
                        options_availability_stage_2,
                        strict=True,
                    )
                    if available
                ],
                ProgramDefinitionOption(
                    option_without_default[0],
                    "Boolean",
                    constraints=ProgramDefinitionConstraints(),
                ),
                ProgramDefinitionOption(
                    option_without_constraints[0],
                    "Boolean",
                ),
            ],
        )
    )

    await client.add_events(
        [
            EventMessage(
                appliance.ha_id,
                EventType.NOTIFY,
                data=ArrayOfEvents(
                    [
                        Event(
                            key=event_key,
                            raw_key=event_key.value,
                            timestamp=0,
                            level="",
                            handling="",
                            value=ProgramKey.DISHCARE_DISHWASHER_AUTO_1,
                        )
                    ]
                ),
            )
        ]
    )
    await hass.async_block_till_done()

    # Verify default values
    # Every time the program is updated, the available options should use the default value if existing
    for entity_id, available in zip(
        option_entity_id.values(), options_availability_stage_2, strict=True
    ):
        assert hass.states.is_state(
            entity_id, STATE_OFF if available else STATE_UNAVAILABLE
        )
    for _, entity_id in (option_without_default, option_without_constraints):
        assert hass.states.is_state(entity_id, STATE_UNKNOWN)