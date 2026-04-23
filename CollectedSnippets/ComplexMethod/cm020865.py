async def test_flow_auth_error_then_password_success(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, mock_homevolt_client: MagicMock
) -> None:
    """Test flow when authentication is required."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    user_input = {
        CONF_HOST: "192.168.1.100",
    }

    mock_homevolt_client.update_info.side_effect = HomevoltAuthenticationError

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "credentials"
    assert result["errors"] == {}

    # Now provide password - should succeed
    mock_homevolt_client.update_info.side_effect = None

    password_input = {
        CONF_PASSWORD: "test-password",
    }

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], password_input
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Homevolt"
    assert result["data"] == {
        CONF_HOST: "192.168.1.100",
        CONF_PASSWORD: "test-password",
    }
    assert result["result"].unique_id == "40580137858664"
    assert len(mock_setup_entry.mock_calls) == 1