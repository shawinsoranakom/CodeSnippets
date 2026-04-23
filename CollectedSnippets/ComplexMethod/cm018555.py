async def test_form_gen1_custom_port(
    hass: HomeAssistant,
    mock_block_device: Mock,
    mock_setup_entry: AsyncMock,
    mock_setup: AsyncMock,
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    with (
        patch(
            "homeassistant.components.shelly.config_flow.get_info",
            return_value={"mac": "test-mac", "type": MODEL_1, "gen": 1},
        ),
        patch(
            "aioshelly.block_device.BlockDevice.create",
            side_effect=CustomPortNotSupported,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "1.1.1.1", CONF_PORT: "1100"},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"]["base"] == "custom_port_not_supported"

    with patch(
        "homeassistant.components.shelly.config_flow.get_info",
        return_value={"mac": "test-mac", "type": MODEL_1, "gen": 1},
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "1.1.1.1", CONF_PORT: DEFAULT_HTTP_PORT},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Test name"
    assert result["data"] == {
        CONF_HOST: "1.1.1.1",
        CONF_PORT: DEFAULT_HTTP_PORT,
        CONF_MODEL: MODEL_1,
        CONF_SLEEP_PERIOD: 0,
        CONF_GEN: 1,
    }
    assert result["context"]["unique_id"] == "test-mac"
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1