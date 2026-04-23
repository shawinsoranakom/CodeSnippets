async def test_binary_sensors_streaming(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_vehicle_data: AsyncMock,
    mock_add_listener: AsyncMock,
) -> None:
    """Tests that the binary sensor entities with streaming are correct."""

    freezer.move_to("2024-01-01 00:00:00+00:00")

    entry = await setup_platform(hass, [Platform.BINARY_SENSOR])

    # Stream update
    mock_add_listener.send(
        {
            "vin": VEHICLE_DATA_ALT["response"]["vin"],
            "data": {
                Signal.FD_WINDOW: "WindowStateOpened",
                Signal.FP_WINDOW: "INVALID_VALUE",
                Signal.RD_WINDOW: "WindowStateClosed",
                Signal.RP_WINDOW: "WindowStatePartiallyOpen",
                Signal.DOOR_STATE: {
                    "DoorState": {
                        "DriverFront": True,
                        "DriverRear": False,
                        "PassengerFront": False,
                        "PassengerRear": False,
                        "TrunkFront": False,
                        "TrunkRear": False,
                    }
                },
                Signal.DRIVER_SEAT_BELT: None,
            },
            "createdAt": "2024-10-04T10:45:17.537Z",
        }
    )
    await hass.async_block_till_done()

    # Reload the entry
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()

    # Assert the entities restored their values with concrete assertions
    assert hass.states.get("binary_sensor.test_front_driver_window").state == "on"
    assert hass.states.get("binary_sensor.test_front_passenger_window").state == "off"
    assert hass.states.get("binary_sensor.test_rear_driver_window").state == "off"
    assert hass.states.get("binary_sensor.test_rear_passenger_window").state == "on"
    assert hass.states.get("binary_sensor.test_front_driver_door").state == "off"
    assert hass.states.get("binary_sensor.test_front_passenger_door").state == "off"
    assert hass.states.get("binary_sensor.test_driver_seat_belt").state == "off"