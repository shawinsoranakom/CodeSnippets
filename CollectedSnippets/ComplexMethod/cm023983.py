async def test_integration_discovery_edit_recovery(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, mock_server: AsyncMock
) -> None:
    """Test editing an integration discovery returns errors and can recover."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_INTEGRATION_DISCOVERY},
        data={CONF_HOST: "1.2.3.4", CONF_PORT: 9000, "uuid": TEST_UUID},
    )

    mock_server.async_query.return_value = False
    mock_server.http_status = HTTPStatus.UNAUTHORIZED

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: "admin", CONF_PASSWORD: "wrongpassword"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "edit_integration_discovered"
    assert result["errors"]["base"] == "invalid_auth"

    mock_server.async_query.return_value = {"uuid": TEST_UUID}
    mock_server.http_status = HTTPStatus.OK

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: "admin", CONF_PASSWORD: "correctpassword"}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].unique_id == TEST_UUID
    assert result["title"] == "1.2.3.4"
    assert len(mock_setup_entry.mock_calls) == 1