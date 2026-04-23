async def test_statistics_sensors(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    zp3111,
    client,
    integration,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test statistics sensors."""

    for prefix, suffixes in (
        (CONTROLLER_STATISTICS_ENTITY_PREFIX, CONTROLLER_STATISTICS_SUFFIXES),
        (CONTROLLER_STATISTICS_ENTITY_PREFIX, CONTROLLER_STATISTICS_SUFFIXES_UNKNOWN),
        (NODE_STATISTICS_ENTITY_PREFIX, NODE_STATISTICS_SUFFIXES),
        (NODE_STATISTICS_ENTITY_PREFIX, NODE_STATISTICS_SUFFIXES_UNKNOWN),
    ):
        for suffix_key in suffixes:
            entry = entity_registry.async_get(f"{prefix}{suffix_key}")
            assert entry, f"Entity {prefix}{suffix_key} not found"
            assert entry.disabled
            assert entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION

            entity_registry.async_update_entity(entry.entity_id, disabled_by=None)

    # reload integration and check if entity is correctly there
    await hass.config_entries.async_reload(integration.entry_id)
    await hass.async_block_till_done()

    for prefix, suffixes, initial_state in (
        (CONTROLLER_STATISTICS_ENTITY_PREFIX, CONTROLLER_STATISTICS_SUFFIXES, "0"),
        (
            CONTROLLER_STATISTICS_ENTITY_PREFIX,
            CONTROLLER_STATISTICS_SUFFIXES_UNKNOWN,
            STATE_UNKNOWN,
        ),
        (NODE_STATISTICS_ENTITY_PREFIX, NODE_STATISTICS_SUFFIXES, "0"),
        (
            NODE_STATISTICS_ENTITY_PREFIX,
            NODE_STATISTICS_SUFFIXES_UNKNOWN,
            STATE_UNKNOWN,
        ),
    ):
        for suffix_key in suffixes:
            entry = entity_registry.async_get(f"{prefix}{suffix_key}")
            assert entry, f"Entity {prefix}{suffix_key} not found"
            assert not entry.disabled
            assert entry.disabled_by is None

            state = hass.states.get(entry.entity_id)
            assert state, f"State for {entry.entity_id} not found"
            assert state.state == initial_state

    # Fire statistics updated for controller
    event = Event(
        "statistics updated",
        {
            "source": "controller",
            "event": "statistics updated",
            "statistics": {
                "messagesTX": 1,
                "messagesRX": 2,
                "messagesDroppedTX": 3,
                "messagesDroppedRX": 4,
                "NAK": 5,
                "CAN": 6,
                "timeoutACK": 7,
                "timeoutResponse": 8,
                "timeoutCallback": 9,
                "backgroundRSSI": {
                    "channel0": {
                        "current": -1,
                        "average": -2,
                    },
                    "channel1": {
                        "current": -3,
                        "average": -4,
                    },
                    "channel2": {
                        "current": -5,
                        "average": -6,
                    },
                    "timestamp": 1681967176510,
                },
            },
        },
    )
    client.driver.controller.receive_event(event)

    # Fire statistics updated event for node
    event = Event(
        "statistics updated",
        {
            "source": "node",
            "event": "statistics updated",
            "nodeId": zp3111.node_id,
            "statistics": {
                "commandsTX": 1,
                "commandsRX": 2,
                "commandsDroppedTX": 3,
                "commandsDroppedRX": 4,
                "timeoutResponse": 5,
                "rtt": 6,
                "rssi": 7,
                "lwr": {
                    "protocolDataRate": 1,
                    "rssi": 1,
                    "repeaters": [],
                    "repeaterRSSI": [],
                    "routeFailedBetween": [],
                },
                "nlwr": {
                    "protocolDataRate": 2,
                    "rssi": 2,
                    "repeaters": [],
                    "repeaterRSSI": [],
                    "routeFailedBetween": [],
                },
                "lastSeen": "2024-01-01T00:00:00+0000",
            },
        },
    )
    zp3111.receive_event(event)

    # Check that states match the statistics from the updates
    for prefix, suffixes in (
        (CONTROLLER_STATISTICS_ENTITY_PREFIX, CONTROLLER_STATISTICS_SUFFIXES),
        (CONTROLLER_STATISTICS_ENTITY_PREFIX, CONTROLLER_STATISTICS_SUFFIXES_UNKNOWN),
        (NODE_STATISTICS_ENTITY_PREFIX, NODE_STATISTICS_SUFFIXES),
        (NODE_STATISTICS_ENTITY_PREFIX, NODE_STATISTICS_SUFFIXES_UNKNOWN),
    ):
        for suffix_key, val in suffixes.items():
            entity_id = f"{prefix}{suffix_key}"
            state = hass.states.get(entity_id)
            assert state
            assert state.state == str(val)

            await hass.services.async_call(
                DOMAIN,
                SERVICE_REFRESH_VALUE,
                {ATTR_ENTITY_ID: entity_id},
                blocking=True,
            )
    await hass.async_block_till_done()
    assert caplog.text.count("There is no value to refresh for this entity") == len(
        [
            *CONTROLLER_STATISTICS_SUFFIXES,
            *CONTROLLER_STATISTICS_SUFFIXES_UNKNOWN,
            *NODE_STATISTICS_SUFFIXES,
            *NODE_STATISTICS_SUFFIXES_UNKNOWN,
        ]
    )