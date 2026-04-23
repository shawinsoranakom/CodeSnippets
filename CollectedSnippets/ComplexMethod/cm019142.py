async def test_program_sensors(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    client: MagicMock,
    config_entry: MockConfigEntry,
    integration_setup: Callable[[MagicMock], Awaitable[bool]],
    appliance: HomeAppliance,
    states: tuple,
    event_run: dict[EventType, dict[EventKey, str | int]],
) -> None:
    """Test sequence for sensors that expose information about a program."""
    entity_ids = ENTITY_ID_STATES.keys()

    time_to_freeze = "2021-01-09 12:00:00+00:00"
    freezer.move_to(time_to_freeze)

    assert config_entry.state is ConfigEntryState.NOT_LOADED
    client.get_status.return_value.status.extend(
        Status(
            key=StatusKey(event_key.value),
            raw_key=event_key.value,
            value=value,
        )
        for event_key, value in EVENT_PROG_DELAYED_START[EventType.STATUS].items()
    )
    assert await integration_setup(client)
    assert config_entry.state is ConfigEntryState.LOADED

    await client.add_events(
        [
            EventMessage(
                appliance.ha_id,
                event_type,
                ArrayOfEvents(
                    [
                        Event(
                            key=event_key,
                            raw_key=event_key.value,
                            timestamp=0,
                            level="",
                            handling="",
                            value=value,
                        )
                    ],
                ),
            )
            for event_type, events in event_run.items()
            for event_key, value in events.items()
        ]
    )
    await hass.async_block_till_done()
    for entity_id, state in zip(entity_ids, states, strict=False):
        assert hass.states.is_state(entity_id, state)