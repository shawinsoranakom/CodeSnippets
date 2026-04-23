async def test_preset_modes_programs_mapping_and_functionality(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    client: MagicMock,
    config_entry: MockConfigEntry,
    integration_setup: Callable[[MagicMock], Awaitable[bool]],
    appliance: HomeAppliance,
    program_keys: list[ProgramKey],
    expected_preset_modes: list[str],
) -> None:
    """Test the preset modes to programs mapping and functionality."""
    client.get_all_programs.side_effect = None
    client.get_all_programs.return_value = ArrayOfPrograms(
        [
            EnumerateProgram(
                key=ProgramKey.HEATING_VENTILATION_AIR_CONDITIONING_AIR_CONDITIONER_AUTO,
                raw_key=ProgramKey.HEATING_VENTILATION_AIR_CONDITIONING_AIR_CONDITIONER_AUTO.value,
                constraints=EnumerateProgramConstraints(
                    execution=Execution.SELECT_AND_START,
                ),
            ),
            *[
                EnumerateProgram(
                    key=program_key,
                    raw_key=program_key.value,
                    constraints=EnumerateProgramConstraints(
                        execution=Execution.SELECT_AND_START,
                    ),
                )
                for program_key in program_keys
            ],
        ]
    )

    assert await integration_setup(client)
    assert config_entry.state is ConfigEntryState.LOADED

    entity = entity_registry.async_get("climate.air_conditioner")
    assert entity
    assert entity.capabilities
    assert entity.capabilities[ATTR_PRESET_MODES] == expected_preset_modes
    state = hass.states.get(entity.entity_id)
    assert state
    assert state.attributes[ATTR_SUPPORTED_FEATURES] & ClimateEntityFeature.PRESET_MODE

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {ATTR_ENTITY_ID: entity.entity_id, ATTR_PRESET_MODE: expected_preset_modes[0]},
        blocking=True,
    )
    await hass.async_block_till_done()

    client.start_program.assert_called_once_with(
        appliance.ha_id, program_key=program_keys[0]
    )
    entity_state = hass.states.get(entity.entity_id)
    assert entity_state
    assert entity_state.attributes[ATTR_PRESET_MODE] == expected_preset_modes[0]