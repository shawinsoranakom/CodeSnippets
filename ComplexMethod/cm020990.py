async def test_create_entry(
    hass: HomeAssistant,
    mock_register_webhook: None,
    mock_external_calls: None,
    mock_generate_secret_token: str,
) -> None:
    """Test user flow."""

    # test: no input

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    assert result["step_id"] == "user"
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None

    # test: invalid proxy url

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_PLATFORM: PLATFORM_WEBHOOKS,
            CONF_API_KEY: "mock api key",
            SECTION_ADVANCED_SETTINGS: {
                CONF_PROXY_URL: "invalid",
            },
        },
    )
    await hass.async_block_till_done()

    assert result["step_id"] == "user"
    assert result["type"] is FlowResultType.FORM
    assert result["errors"]["base"] == "invalid_proxy_url"
    assert result["description_placeholders"]["error_field"] == "proxy url"

    # test: telegram error

    with patch(
        "homeassistant.components.telegram_bot.bot.Bot.get_me",
        side_effect=NetworkError("mock network error"),
    ) as mock_get_me:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_PLATFORM: PLATFORM_WEBHOOKS,
                CONF_API_KEY: "mock api key",
                SECTION_ADVANCED_SETTINGS: {
                    CONF_PROXY_URL: "https://proxy",
                },
            },
        )
        await hass.async_block_till_done()

    mock_get_me.assert_called_once()
    assert result["step_id"] == "user"
    assert result["type"] is FlowResultType.FORM
    assert result["errors"]["base"] == "telegram_error"
    assert result["description_placeholders"]["error_message"] == "mock network error"

    # test: valid input, to continue with webhooks step

    with patch(
        "homeassistant.components.telegram_bot.config_flow.Bot.get_me",
        return_value=User(123456, "Testbot", True),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_PLATFORM: PLATFORM_WEBHOOKS,
                CONF_API_KEY: "mock api key",
                SECTION_ADVANCED_SETTINGS: {
                    CONF_PROXY_URL: "https://proxy",
                },
            },
        )
        await hass.async_block_till_done()

    assert result["step_id"] == "webhooks"
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None

    # test: valid input for webhooks

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_URL: "https://test",
            CONF_TRUSTED_NETWORKS: "149.154.160.0/20",
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Testbot mock last name"
    assert result["data"][CONF_PLATFORM] == PLATFORM_WEBHOOKS
    assert result["data"][CONF_API_KEY] == "mock api key"
    assert result["data"][CONF_PROXY_URL] == "https://proxy"
    assert result["data"][CONF_URL] == "https://test"
    assert result["data"][CONF_TRUSTED_NETWORKS] == ["149.154.160.0/20"]