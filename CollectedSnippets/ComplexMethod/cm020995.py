async def test_duplicate_entry(hass: HomeAssistant) -> None:
    """Test user flow with duplicated entries."""

    data = {
        CONF_PLATFORM: PLATFORM_BROADCAST,
        CONF_API_KEY: "mock api key",
        SECTION_ADVANCED_SETTINGS: {
            CONF_API_ENDPOINT: "http://mock_api_endpoint",
        },
    }

    with patch(
        "homeassistant.components.telegram_bot.config_flow.Bot.get_me",
        return_value=User(123456, "Testbot", True),
    ):
        # test: import first entry success

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data=data,
        )
        await hass.async_block_till_done()

        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_PLATFORM] == PLATFORM_BROADCAST
        assert result["data"][CONF_API_KEY] == "mock api key"
        assert result["data"][CONF_API_ENDPOINT] == "http://mock_api_endpoint"
        assert result["options"][ATTR_PARSER] == PARSER_MD

        # test: import 2nd entry failed due to duplicate

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data=data,
        )
        await hass.async_block_till_done()

        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "already_configured"