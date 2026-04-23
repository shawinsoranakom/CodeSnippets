async def test_credentials_step_invalid_password(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, mock_homevolt_client: MagicMock
) -> None:
    """Test invalid password in credentials step shows error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    user_input = {
        CONF_HOST: "192.168.1.100",
    }

    mock_homevolt_client.update_info.side_effect = HomevoltAuthenticationError

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "credentials"

    # Provide wrong password - should show error
    password_input = {
        CONF_PASSWORD: "wrong-password",
    }

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], password_input
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "credentials"
    assert result["errors"] == {"base": "invalid_auth"}

    mock_homevolt_client.update_info.side_effect = None

    password_input = {
        CONF_PASSWORD: "correct-password",
    }

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], password_input
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Homevolt"
    assert result["data"] == {
        CONF_HOST: "192.168.1.100",
        CONF_PASSWORD: "correct-password",
    }
    assert result["result"].unique_id == "40580137858664"
    assert len(mock_setup_entry.mock_calls) == 1