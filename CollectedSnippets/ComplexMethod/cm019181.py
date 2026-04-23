async def test_supported_features(
    hass: HomeAssistant,
    client: MagicMock,
    config_entry: MockConfigEntry,
    integration_setup: Callable[[MagicMock], Awaitable[bool]],
    appliance: HomeAppliance,
    option_key: OptionKey,
    expected_fan_feature: FanEntityFeature,
) -> None:
    """Test that supported features are detected correctly."""
    client.get_available_program = AsyncMock(
        return_value=ProgramDefinition(
            ProgramKey.UNKNOWN,
            options=[
                ProgramDefinitionOption(
                    option_key,
                    "Enumeration",
                )
            ],
        )
    )

    assert await integration_setup(client)
    assert config_entry.state is ConfigEntryState.LOADED

    entity_id = "fan.air_conditioner"
    state = hass.states.get(entity_id)
    assert state

    assert state.attributes[ATTR_SUPPORTED_FEATURES] & expected_fan_feature

    client.get_available_program = AsyncMock(
        return_value=ProgramDefinition(
            ProgramKey.HEATING_VENTILATION_AIR_CONDITIONING_AIR_CONDITIONER_AUTO,
            options=[],
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
                            key=EventKey.BSH_COMMON_ROOT_ACTIVE_PROGRAM,
                            raw_key=EventKey.BSH_COMMON_ROOT_ACTIVE_PROGRAM.value,
                            timestamp=0,
                            level="",
                            handling="",
                            value=ProgramKey.HEATING_VENTILATION_AIR_CONDITIONING_AIR_CONDITIONER_AUTO,
                        )
                    ]
                ),
            )
        ]
    )
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state
    assert not state.attributes[ATTR_SUPPORTED_FEATURES] & expected_fan_feature

    client.get_available_program = AsyncMock(
        return_value=ProgramDefinition(
            ProgramKey.HEATING_VENTILATION_AIR_CONDITIONING_AIR_CONDITIONER_AUTO,
            options=[
                ProgramDefinitionOption(
                    option_key,
                    "Enumeration",
                )
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
                            key=EventKey.BSH_COMMON_ROOT_ACTIVE_PROGRAM,
                            raw_key=EventKey.BSH_COMMON_ROOT_ACTIVE_PROGRAM.value,
                            timestamp=0,
                            level="",
                            handling="",
                            value=ProgramKey.HEATING_VENTILATION_AIR_CONDITIONING_AIR_CONDITIONER_AUTO.value,
                        )
                    ]
                ),
            )
        ]
    )
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state
    assert state.attributes[ATTR_SUPPORTED_FEATURES] & expected_fan_feature