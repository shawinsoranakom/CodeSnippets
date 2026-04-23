async def test_create_webhook_entry(
    hass: HomeAssistant, api_endpoint: str, webhook_url: str
) -> None:
    """Test user flow that creates a webhook bot."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    assert result["step_id"] == "user"
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None

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
                    CONF_API_ENDPOINT: api_endpoint,
                },
            },
        )
        await hass.async_block_till_done()

    assert result["step_id"] == "webhooks"
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_URL: webhook_url,
            CONF_TRUSTED_NETWORKS: "149.154.160.0/20",
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Testbot"
    assert result["data"][CONF_PLATFORM] == PLATFORM_WEBHOOKS
    assert result["data"][CONF_API_KEY] == "mock api key"
    assert result["data"][CONF_API_ENDPOINT] == api_endpoint
    assert result["data"][CONF_URL] == webhook_url
    assert result["data"][CONF_TRUSTED_NETWORKS] == ["149.154.160.0/20"]