async def test_manual_setup_recovery(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, mock_server: AsyncMock
) -> None:
    """Test manual setup error recovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "edit"}
    )

    mock_server.async_query.return_value = False
    mock_server.http_status = HTTPStatus.UNAUTHORIZED

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "1.2.3.4", CONF_PORT: 9000},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "edit"
    assert result["errors"]["base"] == "invalid_auth"

    mock_server.async_query.return_value = {"uuid": TEST_UUID}
    mock_server.http_status = HTTPStatus.OK

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "1.2.3.4",
            CONF_PORT: 9000,
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "correct_password",
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].unique_id == TEST_UUID
    assert result["title"] == "1.2.3.4"
    assert result["data"][CONF_HOST] == "1.2.3.4"
    assert len(mock_setup_entry.mock_calls) == 1