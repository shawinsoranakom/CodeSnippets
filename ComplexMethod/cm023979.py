async def test_manual_setup(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, mock_server: AsyncMock
) -> None:
    """Test we can finish a manual setup successfully."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "edit"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "edit"

    mock_server.async_query.return_value = {"uuid": TEST_UUID}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "1.2.3.4", CONF_PORT: 9000},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].unique_id == TEST_UUID
    assert result["title"] == "1.2.3.4"
    assert result["data"][CONF_HOST] == "1.2.3.4"
    assert len(mock_setup_entry.mock_calls) == 1