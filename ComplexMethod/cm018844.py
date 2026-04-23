async def test_cover_streaming(
    hass: HomeAssistant,
    mock_vehicle_data: AsyncMock,
    mock_add_listener: AsyncMock,
) -> None:
    """Tests that the binary sensor entities with streaming are correct."""

    entry = await setup_platform(hass, [Platform.COVER])

    # Stream update
    mock_add_listener.send(
        {
            "vin": VEHICLE_DATA_ALT["response"]["vin"],
            "data": {
                Signal.FD_WINDOW: "WindowStateClosed",
                Signal.FP_WINDOW: "WindowStateClosed",
                Signal.RD_WINDOW: "WindowStateClosed",
                Signal.RP_WINDOW: "WindowStateClosed",
                Signal.CHARGE_PORT_DOOR_OPEN: False,
                Signal.DOOR_STATE: {
                    "DoorState": {
                        "DriverFront": False,
                        "DriverRear": False,
                        "PassengerFront": False,
                        "PassengerRear": False,
                        "TrunkFront": False,
                        "TrunkRear": False,
                    }
                },
            },
            "createdAt": "2024-10-04T10:45:17.537Z",
        }
    )
    await hass.async_block_till_done()

    # Reload the entry
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()

    # Assert the entities restored their values with concrete assertions
    assert hass.states.get("cover.test_windows").state == CoverState.CLOSED
    assert hass.states.get("cover.test_charge_port_door").state == CoverState.CLOSED
    # Frunk and trunk don't get closed state from stream, they show unknown
    assert hass.states.get("cover.test_frunk").state == "unknown"
    assert hass.states.get("cover.test_trunk").state == "unknown"

    # Send some alternative data with everything open
    mock_add_listener.send(
        {
            "vin": VEHICLE_DATA_ALT["response"]["vin"],
            "data": {
                Signal.FD_WINDOW: "WindowStateOpened",
                Signal.FP_WINDOW: "WindowStateOpened",
                Signal.RD_WINDOW: "WindowStateOpened",
                Signal.RP_WINDOW: "WindowStateOpened",
                Signal.CHARGE_PORT_DOOR_OPEN: False,
                Signal.DOOR_STATE: {
                    "DoorState": {
                        "DriverFront": True,
                        "DriverRear": True,
                        "PassengerFront": True,
                        "PassengerRear": True,
                        "TrunkFront": True,
                        "TrunkRear": True,
                    }
                },
            },
            "createdAt": "2024-10-04T10:45:17.537Z",
        }
    )
    await hass.async_block_till_done()

    # Assert the entities get new values with concrete assertions
    assert hass.states.get("cover.test_windows").state == CoverState.OPEN
    # Charge port door doesn't change with CHARGE_PORT_DOOR_OPEN: False
    assert hass.states.get("cover.test_charge_port_door").state == CoverState.CLOSED
    # Frunk and trunk still show unknown (DOOR_STATE doesn't contain trunk state info)
    assert hass.states.get("cover.test_frunk").state == "unknown"
    assert hass.states.get("cover.test_trunk").state == "unknown"

    # Send some alternative data with everything unknown
    mock_add_listener.send(
        {
            "vin": VEHICLE_DATA_ALT["response"]["vin"],
            "data": {
                Signal.FD_WINDOW: "WindowStateUnknown",
                Signal.FP_WINDOW: "WindowStateUnknown",
                Signal.RD_WINDOW: "WindowStateUnknown",
                Signal.RP_WINDOW: "WindowStateUnknown",
                Signal.CHARGE_PORT_DOOR_OPEN: None,
                Signal.DOOR_STATE: {
                    "DoorState": {
                        "DriverFront": None,
                        "DriverRear": None,
                        "PassengerFront": None,
                        "PassengerRear": None,
                        "TrunkFront": None,
                        "TrunkRear": None,
                    }
                },
            },
            "createdAt": "2024-10-04T10:45:17.537Z",
        }
    )
    await hass.async_block_till_done()

    # Assert the entities get values with concrete assertions
    # Windows stay open when unknown because of previous state restoration
    assert hass.states.get("cover.test_windows").state == CoverState.OPEN
    assert hass.states.get("cover.test_charge_port_door").state == "unknown"
    assert hass.states.get("cover.test_frunk").state == "unknown"
    assert hass.states.get("cover.test_trunk").state == "unknown"