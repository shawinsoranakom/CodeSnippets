async def test_invalid_api_key(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_async_client_api_error: AsyncMock,
    request: pytest.FixtureRequest,
) -> None:
    """Test user step with invalid api key."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert not result["errors"]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_API_KEY: "api_key",
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_api_key"}

    mock_setup_entry.assert_not_called()

    # Use a working client
    request.getfixturevalue("mock_async_client")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_API_KEY: "api_key",
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "ElevenLabs"
    assert result["data"] == {
        "api_key": "api_key",
    }
    assert result["options"] == {
        CONF_MODEL: DEFAULT_TTS_MODEL,
        CONF_VOICE: "voice1",
        CONF_STT_MODEL: DEFAULT_STT_MODEL,
        CONF_STT_AUTO_LANGUAGE: False,
    }

    mock_setup_entry.assert_called_once()