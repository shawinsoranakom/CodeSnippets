async def test_form_auth_errors_test_connection_gen2(
    hass: HomeAssistant,
    mock_rpc_device: Mock,
    mock_setup: AsyncMock,
    mock_setup_entry: AsyncMock,
    exc: Exception,
    base_error: str,
) -> None:
    """Test we handle errors in Gen2 authenticated devices."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.shelly.config_flow.get_info",
        return_value={"mac": "test-mac", "auth": True, "gen": 2},
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "1.1.1.1"},
        )

    with patch(
        "aioshelly.rpc_device.RpcDevice.create",
        side_effect=exc,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_PASSWORD: "test password"}
        )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": base_error}

    with patch(
        "homeassistant.components.shelly.config_flow.get_info",
        return_value={"mac": "test-mac", "auth": True, "gen": 2},
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PASSWORD: "test password"},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Test name"
    assert result["data"] == {
        CONF_HOST: "1.1.1.1",
        CONF_PORT: DEFAULT_HTTP_PORT,
        CONF_MODEL: "SNSW-002P16EU",
        CONF_SLEEP_PERIOD: 0,
        CONF_GEN: 2,
        CONF_USERNAME: "admin",
        CONF_PASSWORD: "test password",
    }
    assert result["context"]["unique_id"] == "test-mac"
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1