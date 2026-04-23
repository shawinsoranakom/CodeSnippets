async def test_reconfigure_flow_broadcast(
    hass: HomeAssistant,
    mock_register_webhook: None,
    mock_external_calls: None,
    mock_webhooks_config_entry: MockConfigEntry,
) -> None:
    """Test reconfigure flow for broadcast bot."""
    mock_webhooks_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_webhooks_config_entry.entry_id)
    await hass.async_block_till_done()

    result = await mock_webhooks_config_entry.start_reconfigure_flow(hass)
    assert result["step_id"] == "reconfigure"
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None

    # test: invalid proxy url

    with patch(
        "homeassistant.components.telegram_bot.config_flow.Bot.get_me",
    ) as mock_bot:
        mock_bot.side_effect = NetworkError("mock invalid proxy")

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_PLATFORM: PLATFORM_BROADCAST,
                SECTION_ADVANCED_SETTINGS: {
                    CONF_PROXY_URL: "invalid",
                },
            },
        )
        await hass.async_block_till_done()

    assert result["step_id"] == "reconfigure"
    assert result["type"] is FlowResultType.FORM
    assert result["errors"]["base"] == "invalid_proxy_url"

    # test: valid

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_PLATFORM: PLATFORM_BROADCAST,
            SECTION_ADVANCED_SETTINGS: {
                CONF_PROXY_URL: "https://test",
            },
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert mock_webhooks_config_entry.data[CONF_PLATFORM] == PLATFORM_BROADCAST
    assert mock_webhooks_config_entry.data[CONF_PROXY_URL] == "https://test"

    service: TelegramNotificationService = mock_webhooks_config_entry.runtime_data
    assert (
        service.bot._request[0]._client_kwargs["proxy"].url == "https://test"
    )  # get updates request
    assert (
        service.bot._request[1]._client_kwargs["proxy"].url == "https://test"
    )