async def test_zeroconf(
    hass: HomeAssistant,
    gen: int,
    model: str,
    get_info: dict[str, Any],
    mock_block_device: Mock,
    mock_rpc_device: Mock,
    mock_setup_entry: AsyncMock,
    mock_setup: AsyncMock,
) -> None:
    """Test we get the form."""

    with patch(
        "homeassistant.components.shelly.config_flow.get_info", return_value=get_info
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            data=DISCOVERY_INFO,
            context={"source": config_entries.SOURCE_ZEROCONF},
        )
        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {}
        context = next(
            flow["context"]
            for flow in hass.config_entries.flow.async_progress()
            if flow["flow_id"] == result["flow_id"]
        )
        assert context["title_placeholders"]["name"] == "shelly1pm-12345"
        assert context["confirm_only"] is True

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Test name"
    assert result["data"] == {
        CONF_HOST: "1.1.1.1",
        CONF_MODEL: model,
        CONF_SLEEP_PERIOD: 0,
        CONF_GEN: gen,
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1