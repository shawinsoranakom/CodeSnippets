async def test_discovery_flow_edit_discovered_success(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_server: AsyncMock,
    mock_discover: MagicMock,
) -> None:
    """Test the successful outcome of the edit_discovered step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "start_discovery"}
    )
    await hass.async_block_till_done()
    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    mock_server.http_status = HTTPStatus.UNAUTHORIZED
    mock_server.async_query.return_value = False

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_SERVER_LIST: "1.1.1.1"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "edit_discovered"

    mock_server.http_status = HTTPStatus.OK
    mock_server.async_query.side_effect = [False, {"uuid": TEST_UUID}]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: "admin", CONF_PASSWORD: "password"}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "1.1.1.1"
    assert result["data"][CONF_HOST] == "1.1.1.1"
    assert result["data"][CONF_USERNAME] == "admin"
    assert result["data"][CONF_PASSWORD] == "password"
    assert len(mock_setup_entry.mock_calls) == 1