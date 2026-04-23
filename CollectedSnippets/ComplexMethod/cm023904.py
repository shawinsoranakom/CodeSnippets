async def test_new_door_entities_created_on_refresh(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_client: MagicMock,
) -> None:
    """Test that new door entities are added dynamically via coordinator listener."""
    # Verify new door entities do not exist yet
    assert not hass.states.get("binary_sensor.garage_door")
    assert not hass.states.get("button.garage_door_unlock")
    assert not hass.states.get("event.garage_door_doorbell")
    assert not hass.states.get("event.garage_door_access")
    assert not hass.states.get("image.garage_door_thumbnail")

    # Add a new door to the API response
    mock_client.get_doors.return_value = [
        *mock_client.get_doors.return_value,
        _make_door(
            "door-003",
            "Garage Door",
            door_thumbnail="/preview/garage_door.png",
            door_thumbnail_last_update=1700000000,
        ),
    ]

    # Trigger natural refresh via WebSocket reconnect
    on_disconnect = mock_client.start_websocket.call_args[1]["on_disconnect"]
    on_connect = mock_client.start_websocket.call_args[1]["on_connect"]
    on_disconnect()
    await hass.async_block_till_done()
    on_connect()
    await hass.async_block_till_done()

    # Entities for the new door should now exist
    assert hass.states.get("binary_sensor.garage_door")
    assert hass.states.get("button.garage_door_unlock")
    assert hass.states.get("event.garage_door_doorbell")
    assert hass.states.get("event.garage_door_access")
    assert hass.states.get("image.garage_door_thumbnail")