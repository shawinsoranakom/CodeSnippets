async def test_rssi_sensor_error(
    hass: HomeAssistant,
    zp3111: Node,
    integration: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test rssi sensor error."""
    entity_id = "sensor.4_in_1_sensor_signal_strength"

    entity_registry.async_update_entity(entity_id, disabled_by=None)

    # reload integration and check if entity is correctly there
    await hass.config_entries.async_reload(integration.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state
    assert state.state == "unknown"

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
                "rssi": 7,  # baseline
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
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state
    assert state.state == "7"

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
                "rssi": 125,  # no signal detected
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
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state
    assert state.state == "unknown"

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
                "rssi": 127,  # not available
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
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state
    assert state.state == "unavailable"

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
                "rssi": 126,  # receiver saturated
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
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state
    assert state.state == "unknown"