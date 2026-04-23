async def test_subentry_flow(
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
    assert result["description_placeholders"] == {
        **DESCRIPTION_PLACEHOLDERS,
        "bot_username": "@mock_bot",
        "bot_url": "https://t.me/mock_bot",
        "most_recent_chat": "mock first_name (123456)",
    }

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={CONF_CHAT_ID: 987654321},
    )
    await hass.async_block_till_done()

    subentry_id = list(mock_broadcast_config_entry.subentries)[-1]
    subentry: ConfigSubentry = mock_broadcast_config_entry.subentries[subentry_id]

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert subentry.subentry_type == SUBENTRY_TYPE_ALLOWED_CHAT_IDS
    assert subentry.title == "mock title"
    assert subentry.unique_id == "987654321"
    assert subentry.data == {CONF_CHAT_ID: 987654321}