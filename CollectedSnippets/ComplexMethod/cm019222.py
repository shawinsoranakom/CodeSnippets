async def test_services(hass: HomeAssistant, mock_device: MagicMock) -> None:
    """Test service calls."""
    await hass.services.async_call(
        MEDIA_PLAYER_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )
    assert mock_device.leave_standby.call_count == 1

    await hass.services.async_call(
        MEDIA_PLAYER_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )
    assert mock_device.enter_standby.call_count == 1

    await hass.services.async_call(
        MEDIA_PLAYER_DOMAIN,
        SERVICE_MEDIA_PLAY,
        {ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )
    assert mock_device.play.call_count == 1

    await hass.services.async_call(
        MEDIA_PLAYER_DOMAIN,
        SERVICE_MEDIA_PAUSE,
        {ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )
    assert mock_device.pause.call_count == 1

    await hass.services.async_call(
        MEDIA_PLAYER_DOMAIN,
        SERVICE_MEDIA_STOP,
        {ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )
    assert mock_device.stop.call_count == 1

    await hass.services.async_call(
        MEDIA_PLAYER_DOMAIN,
        SERVICE_MEDIA_NEXT_TRACK,
        {ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )
    assert mock_device.next.call_count == 1

    await hass.services.async_call(
        MEDIA_PLAYER_DOMAIN,
        SERVICE_MEDIA_PREVIOUS_TRACK,
        {ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )
    assert mock_device.previous.call_count == 1