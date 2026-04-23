async def test_discovery_flow_success(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_server: AsyncMock,
    mock_discover: MagicMock,
) -> None:
    """Test discovery flow where default connect succeeds immediately."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "start_discovery"}
    )

    assert result["type"] is FlowResultType.SHOW_PROGRESS
    assert result["step_id"] == "start_discovery"

    await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "choose_server"

    mock_server.async_query.return_value = {"uuid": TEST_UUID}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_SERVER_LIST: "1.1.1.1"}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].unique_id == TEST_UUID
    assert result["title"] == "1.1.1.1"
    assert len(mock_setup_entry.mock_calls) == 1