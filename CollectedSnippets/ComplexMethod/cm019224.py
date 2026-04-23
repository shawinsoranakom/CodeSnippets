async def test_commands(hass: HomeAssistant, mock_device: MagicMock) -> None:
    """Test service calls."""
    await hass.services.async_call(
        REMOTE_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )
    assert mock_device.leave_standby.call_count == 1

    await hass.services.async_call(
        REMOTE_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )
    assert mock_device.enter_standby.call_count == 1

    await hass.services.async_call(
        REMOTE_DOMAIN,
        SERVICE_SEND_COMMAND,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_COMMAND: ["select"]},
        blocking=True,
    )
    assert mock_device.select.call_count == 1

    await hass.services.async_call(
        REMOTE_DOMAIN,
        SERVICE_SEND_COMMAND,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_COMMAND: ["up"]},
        blocking=True,
    )
    assert mock_device.up.call_count == 1

    await hass.services.async_call(
        REMOTE_DOMAIN,
        SERVICE_SEND_COMMAND,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_COMMAND: ["down"]},
        blocking=True,
    )
    assert mock_device.down.call_count == 1

    await hass.services.async_call(
        REMOTE_DOMAIN,
        SERVICE_SEND_COMMAND,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_COMMAND: ["left"]},
        blocking=True,
    )
    assert mock_device.left.call_count == 1

    await hass.services.async_call(
        REMOTE_DOMAIN,
        SERVICE_SEND_COMMAND,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_COMMAND: ["right"]},
        blocking=True,
    )
    assert mock_device.right.call_count == 1

    await hass.services.async_call(
        REMOTE_DOMAIN,
        SERVICE_SEND_COMMAND,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_COMMAND: ["cancel"]},
        blocking=True,
    )
    assert mock_device.cancel.call_count == 1

    await hass.services.async_call(
        REMOTE_DOMAIN,
        SERVICE_SEND_COMMAND,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_COMMAND: ["replay"]},
        blocking=True,
    )
    assert mock_device.replay.call_count == 1

    await hass.services.async_call(
        REMOTE_DOMAIN,
        SERVICE_SEND_COMMAND,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_COMMAND: ["scan_forward"]},
        blocking=True,
    )
    assert mock_device.scan_forward.call_count == 1

    await hass.services.async_call(
        REMOTE_DOMAIN,
        SERVICE_SEND_COMMAND,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_COMMAND: ["scan_reverse"]},
        blocking=True,
    )
    assert mock_device.scan_reverse.call_count == 1

    await hass.services.async_call(
        REMOTE_DOMAIN,
        SERVICE_SEND_COMMAND,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_COMMAND: ["go_movie_covers"]},
        blocking=True,
    )
    assert mock_device.go_movie_covers.call_count == 1

    await hass.services.async_call(
        REMOTE_DOMAIN,
        SERVICE_SEND_COMMAND,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_COMMAND: ["menu_toggle"]},
        blocking=True,
    )
    assert mock_device.menu_toggle.call_count == 1