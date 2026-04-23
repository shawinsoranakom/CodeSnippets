async def test_send_message(
    hass: HomeAssistant, webhook_bot, service: str, input: dict[str, Any]
) -> None:
    """Test the send_message service. Tests any service that does not require files to be sent."""
    context = Context()
    events = async_capture_events(hass, "telegram_sent")

    response = await hass.services.async_call(
        DOMAIN,
        service,
        input,
        blocking=True,
        context=context,
        return_response=True,
    )
    await hass.async_block_till_done()

    assert len(events) == 1
    assert events[0].context == context

    assert events[0].data["bot"]["id"] == 123456
    assert events[0].data["bot"]["first_name"] == "Testbot"
    assert events[0].data["bot"]["last_name"] == "mock last name"
    assert events[0].data["bot"]["username"] == "mock_bot"

    assert response == {
        "chats": [
            {
                ATTR_CHAT_ID: 12345678,
                ATTR_MESSAGE_ID: 12345,
                ATTR_ENTITY_ID: "notify.mock_title_mock_chat",
            }
        ]
    }