async def test_step_user_errors(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_homevolt_client: MagicMock,
    exception: Exception,
    expected_error: str,
) -> None:
    """Test error cases for the user step with recovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    user_input = {
        CONF_HOST: "192.168.1.100",
    }

    mock_homevolt_client.update_info.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": expected_error}

    mock_homevolt_client.update_info.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input,
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Homevolt"
    assert result["data"] == {CONF_HOST: "192.168.1.100", CONF_PASSWORD: None}
    assert result["result"].unique_id == "40580137858664"
    assert len(mock_setup_entry.mock_calls) == 1