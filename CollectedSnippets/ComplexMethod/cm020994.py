async def test_subentry_flow_chat_error(
    hass: HomeAssistant,
    mock_broadcast_config_entry: MockConfigEntry,
    mock_external_calls: None,
) -> None:
    """Test subentry flow."""
    mock_broadcast_config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(mock_broadcast_config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.subentries.async_init(
        (mock_broadcast_config_entry.entry_id, SUBENTRY_TYPE_ALLOWED_CHAT_IDS),
        context={"source": SOURCE_USER},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    # test: network error

    with patch("homeassistant.components.telegram_bot.bot.Bot.get_chat") as mock_bot:
        mock_bot.side_effect = NetworkError("mock network error")

        result = await hass.config_entries.subentries.async_configure(
            result["flow_id"],
            user_input={CONF_CHAT_ID: 1234567890},
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"]["base"] == "telegram_error"
    assert result["description_placeholders"]["error_message"] == "mock network error"

    # test: chat not found

    with patch("homeassistant.components.telegram_bot.bot.Bot.get_chat") as mock_bot:
        mock_bot.side_effect = BadRequest("mock chat not found")

        result = await hass.config_entries.subentries.async_configure(
            result["flow_id"],
            user_input={CONF_CHAT_ID: 1234567890},
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"]["base"] == "chat_not_found"

    # test: chat id already configured

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={CONF_CHAT_ID: 123456},
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"