async def test_number_entity_availability(
    hass: HomeAssistant,
    client: MagicMock,
    config_entry: MockConfigEntry,
    integration_setup: Callable[[MagicMock], Awaitable[bool]],
    appliance: HomeAppliance,
) -> None:
    """Test if number entities availability are based on the appliance connection state."""
    entity_ids = [
        f"{NUMBER_DOMAIN.lower()}.oven_alarm_clock",
        f"{NUMBER_DOMAIN.lower()}.oven_setpoint_temperature",
    ]
    client.get_available_program = AsyncMock(
        return_value=ProgramDefinition(
            ProgramKey.UNKNOWN,
            options=[
                ProgramDefinitionOption(
                    OptionKey.COOKING_OVEN_SETPOINT_TEMPERATURE, "Boolean"
                )
            ],
        )
    )

    client.get_setting.side_effect = None
    # Setting constrains are not needed for this test
    # so we rise an error to easily test the availability
    client.get_setting = AsyncMock(side_effect=HomeConnectError())
    assert await integration_setup(client)
    assert config_entry.state is ConfigEntryState.LOADED

    for entity_id in entity_ids:
        state = hass.states.get(entity_id)
        assert state
        assert state.state != STATE_UNAVAILABLE

    await client.add_events(
        [
            EventMessage(
                appliance.ha_id,
                EventType.DISCONNECTED,
                ArrayOfEvents([]),
            )
        ]
    )
    await hass.async_block_till_done()

    for entity_id in entity_ids:
        assert hass.states.is_state(entity_id, STATE_UNAVAILABLE)

    await client.add_events(
        [
            EventMessage(
                appliance.ha_id,
                EventType.CONNECTED,
                ArrayOfEvents([]),
            )
        ]
    )
    await hass.async_block_till_done()

    for entity_id in entity_ids:
        state = hass.states.get(entity_id)
        assert state
        assert state.state != STATE_UNAVAILABLE