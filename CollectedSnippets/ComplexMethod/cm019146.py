async def test_filter_programs(
    entity_registry: er.EntityRegistry,
    client: MagicMock,
    config_entry: MockConfigEntry,
    integration_setup: Callable[[MagicMock], Awaitable[bool]],
) -> None:
    """Test select that only right programs are shown."""
    client.get_all_programs.side_effect = None
    client.get_all_programs.return_value = ArrayOfPrograms(
        [
            EnumerateProgram(
                key=ProgramKey.DISHCARE_DISHWASHER_ECO_50,
                raw_key=ProgramKey.DISHCARE_DISHWASHER_ECO_50.value,
                constraints=EnumerateProgramConstraints(
                    execution=Execution.SELECT_ONLY,
                ),
            ),
            EnumerateProgram(
                key=ProgramKey.UNKNOWN,
                raw_key="an unknown program",
            ),
            EnumerateProgram(
                key=ProgramKey.DISHCARE_DISHWASHER_QUICK_45,
                raw_key=ProgramKey.DISHCARE_DISHWASHER_QUICK_45.value,
                constraints=EnumerateProgramConstraints(
                    execution=Execution.START_ONLY,
                ),
            ),
            EnumerateProgram(
                key=ProgramKey.DISHCARE_DISHWASHER_AUTO_1,
                raw_key=ProgramKey.DISHCARE_DISHWASHER_AUTO_1.value,
                constraints=EnumerateProgramConstraints(
                    execution=Execution.SELECT_AND_START,
                ),
            ),
        ]
    )

    assert await integration_setup(client)
    assert config_entry.state is ConfigEntryState.LOADED

    entity = entity_registry.async_get("select.dishwasher_selected_program")
    assert entity
    assert entity.capabilities
    assert entity.capabilities[ATTR_OPTIONS] == [
        "dishcare_dishwasher_program_eco_50",
        "dishcare_dishwasher_program_auto_1",
    ]

    entity = entity_registry.async_get("select.dishwasher_active_program")
    assert entity
    assert entity.capabilities
    assert entity.capabilities[ATTR_OPTIONS] == [
        "dishcare_dishwasher_program_quick_45",
        "dishcare_dishwasher_program_auto_1",
    ]