async def test_form(
    hass: HomeAssistant,
    gen: int,
    model: str,
    port: int,
    mock_block_device: Mock,
    mock_rpc_device: Mock,
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
            return_value={
                "mac": "test-mac",
                "type": MODEL_1,
                "auth": False,
                "gen": gen,
                "port": port,
            },
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "1.1.1.1", CONF_PORT: port},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Test name"
    assert result["data"] == {
        CONF_HOST: "1.1.1.1",
        CONF_PORT: port,
        CONF_MODEL: model,
        CONF_SLEEP_PERIOD: 0,
        CONF_GEN: gen,
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1