async def test_zeroconf_require_auth(
    hass: HomeAssistant,
    mock_block_device: Mock,
    mock_setup_entry: AsyncMock,
    mock_setup: AsyncMock,
) -> None:
    """Test zeroconf if auth is required."""

    with patch(
        "homeassistant.components.shelly.config_flow.get_info",
        return_value={"mac": "test-mac", "type": MODEL_1, "auth": True},
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            data=DISCOVERY_INFO,
            context={"source": config_entries.SOURCE_ZEROCONF},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "test username", CONF_PASSWORD: "test password"},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Test name"
    assert result["data"] == {
        CONF_HOST: "1.1.1.1",
        CONF_PORT: DEFAULT_HTTP_PORT,
        CONF_MODEL: MODEL_1,
        CONF_SLEEP_PERIOD: 0,
        CONF_GEN: 1,
        CONF_USERNAME: "test username",
        CONF_PASSWORD: "test password",
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1