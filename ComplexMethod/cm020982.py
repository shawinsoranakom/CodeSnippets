async def test_webhook_callback_inline_keyboard(
    hass: HomeAssistant,
    webhook_bot: None,
    hass_client: ClientSessionGenerator,
    update_callback_inline_keyboard,
    mock_generate_secret_token,
) -> None:
    """Test callback query triggered by inline keyboard button."""
    client = await hass_client()
    events = async_capture_events(hass, "telegram_callback")

    response = await client.post(
        f"{TELEGRAM_WEBHOOK_URL}_123456",
        json=update_callback_inline_keyboard,
        headers={"X-Telegram-Bot-Api-Secret-Token": mock_generate_secret_token},
    )
    assert response.status == 200
    assert (await response.read()).decode("utf-8") == ""

    # Make sure event has fired
    await hass.async_block_till_done()

    assert len(events) == 1
    assert (
        events[0].data["chat_id"]
        == update_callback_inline_keyboard["callback_query"]["message"]["chat"]["id"]
    )
    expected_message = {
        **update_callback_inline_keyboard["callback_query"]["message"],
        "delete_chat_photo": False,
        "group_chat_created": False,
        "supergroup_chat_created": False,
        "channel_chat_created": False,
    }
    assert events[0].data["message"] == expected_message
    assert events[0].data["data"] == "/command arg1 arg2"
    assert events[0].data["command"] == "/command"
    assert events[0].data["args"] == ["arg1", "arg2"]
    assert isinstance(events[0].context, Context)