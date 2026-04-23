async def test_send_msg(hass: HomeAssistant) -> None:
    """Test notify.events service."""
    notify_calls = async_mock_service(hass, NOTIFY_DOMAIN, "events")

    await hass.services.async_call(
        NOTIFY_DOMAIN,
        "events",
        {
            ATTR_MESSAGE: "message content",
            ATTR_DATA: {
                ATTR_TOKEN: "XYZ",
                ATTR_LEVEL: "warning",
                ATTR_PRIORITY: "high",
            },
        },
        blocking=True,
    )

    assert len(notify_calls) == 1
    call = notify_calls[-1]

    assert call.domain == NOTIFY_DOMAIN
    assert call.service == "events"
    assert call.data.get(ATTR_MESSAGE) == "message content"
    assert call.data.get(ATTR_DATA).get(ATTR_TOKEN) == "XYZ"
    assert call.data.get(ATTR_DATA).get(ATTR_LEVEL) == "warning"
    assert call.data.get(ATTR_DATA).get(ATTR_PRIORITY) == "high"