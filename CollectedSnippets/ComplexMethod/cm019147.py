async def test_programs_updated_on_connect(
    hass: HomeAssistant,
    client: MagicMock,
    config_entry: MockConfigEntry,
    integration_setup: Callable[[MagicMock], Awaitable[bool]],
    appliance: HomeAppliance,
) -> None:
    """Test that devices reconnected.

    Specifically those devices whose settings, status, etc. could
    not be obtained while disconnected and once connected, the entities are added.
    """
    get_all_programs_mock = client.get_all_programs

    returned_programs = (
        await get_all_programs_mock.side_effect(appliance.ha_id)
    ).programs
    assert len(returned_programs) > 1

    async def get_all_programs_side_effect(ha_id: str):
        if ha_id == appliance.ha_id:
            return ArrayOfPrograms(returned_programs[:1])
        return await get_all_programs_mock.side_effect(ha_id)

    client.get_all_programs = AsyncMock(side_effect=get_all_programs_side_effect)
    assert await integration_setup(client)
    assert config_entry.state is ConfigEntryState.LOADED
    client.get_all_programs = get_all_programs_mock

    state = hass.states.get("select.washer_active_program")
    assert state
    programs = state.attributes[ATTR_OPTIONS]

    await client.add_events(
        [
            EventMessage(
                appliance.ha_id,
                EventType.CONNECTED,
                data=ArrayOfEvents([]),
            )
        ]
    )
    await hass.async_block_till_done()

    state = hass.states.get("select.washer_active_program")
    assert state
    assert state.attributes[ATTR_OPTIONS] != programs
    assert len(state.attributes[ATTR_OPTIONS]) > len(programs)