async def test_notify(hass: HomeAssistant, client) -> None:
    """Test sending a message."""
    await setup_webostv(hass)
    assert hass.services.has_service(NOTIFY_DOMAIN, SERVICE_NAME)

    await hass.services.async_call(
        NOTIFY_DOMAIN,
        SERVICE_NAME,
        {
            ATTR_MESSAGE: MESSAGE,
            ATTR_DATA: {
                ATTR_ICON: ICON_PATH,
            },
        },
        blocking=True,
    )
    assert client.mock_calls[0] == call.connect()
    assert client.connect.call_count == 1
    client.send_message.assert_called_with(MESSAGE, icon_path=ICON_PATH)

    await hass.services.async_call(
        NOTIFY_DOMAIN,
        SERVICE_NAME,
        {
            ATTR_MESSAGE: MESSAGE,
            ATTR_DATA: {
                "OTHER_DATA": "not_used",
            },
        },
        blocking=True,
    )
    assert client.mock_calls[0] == call.connect()
    assert client.connect.call_count == 1
    client.send_message.assert_called_with(MESSAGE, icon_path=None)

    await hass.services.async_call(
        NOTIFY_DOMAIN,
        SERVICE_NAME,
        {
            ATTR_MESSAGE: "only message, no data",
        },
        blocking=True,
    )

    assert client.connect.call_count == 1
    assert client.send_message.call_args == call(
        "only message, no data", icon_path=None
    )