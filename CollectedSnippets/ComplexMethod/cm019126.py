async def test_hvac_modes_programs_mapping_and_functionality(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    client: MagicMock,
    config_entry: MockConfigEntry,
    integration_setup: Callable[[MagicMock], Awaitable[bool]],
    appliance: HomeAppliance,
    expected_hvac_modes: list[HVACMode],
    program_keys: list[ProgramKey],
) -> None:
    """Test the HVAC modes to programs mapping."""
    client.get_all_programs.side_effect = None
    client.get_all_programs.return_value = ArrayOfPrograms(
        [
            EnumerateProgram(
                key=program_key,
                raw_key=program_key.value,
                constraints=EnumerateProgramConstraints(
                    execution=Execution.SELECT_AND_START,
                ),
            )
            for program_key in program_keys
        ]
    )

    assert await integration_setup(client)
    assert config_entry.state is ConfigEntryState.LOADED

    entity = entity_registry.async_get("climate.air_conditioner")
    assert entity
    assert entity.capabilities
    assert entity.capabilities[ATTR_HVAC_MODES] == [*expected_hvac_modes, HVACMode.OFF]
    assert entity.supported_features & (
        ClimateEntityFeature.TURN_ON | ClimateEntityFeature.TURN_OFF
    )

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: entity.entity_id, ATTR_HVAC_MODE: expected_hvac_modes[0]},
        blocking=True,
    )
    await hass.async_block_till_done()

    client.start_program.assert_called_once_with(
        appliance.ha_id, program_key=program_keys[0]
    )
    assert hass.states.is_state(entity.entity_id, expected_hvac_modes[0])