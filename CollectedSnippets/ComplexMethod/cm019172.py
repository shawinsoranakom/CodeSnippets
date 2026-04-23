async def test_event_listener_resilience(
    hass: HomeAssistant,
    client: MagicMock,
    config_entry: MockConfigEntry,
    integration_setup: Callable[[MagicMock], Awaitable[bool]],
    appliance: HomeAppliance,
    exception: HomeConnectError,
    entity_id: str,
    initial_state: str,
    event_key: EventKey,
    event_value: Any,
    after_event_expected_state: str,
) -> None:
    """Test that the event listener is resilient to interruptions."""
    future = hass.loop.create_future()

    async def stream_exception():
        yield await future

    client.stream_all_events = MagicMock(
        side_effect=[stream_exception(), client.stream_all_events()]
    )

    await integration_setup(client)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED
    assert len(config_entry._background_tasks) == 1

    state = hass.states.get(entity_id)
    assert state
    assert state.state == initial_state

    future.set_exception(exception)
    await hass.async_block_till_done()

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=30))
    await hass.async_block_till_done()

    assert client.stream_all_events.call_count == 2

    await client.add_events(
        [
            EventMessage(
                appliance.ha_id,
                EventType.STATUS,
                ArrayOfEvents(
                    [
                        Event(
                            key=event_key,
                            raw_key=event_key.value,
                            timestamp=0,
                            level="",
                            handling="",
                            value=event_value,
                        )
                    ],
                ),
            ),
        ]
    )
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state
    assert state.state == after_event_expected_state