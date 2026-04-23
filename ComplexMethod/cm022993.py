async def test_user_flow_device_bad_connection_then_success(
    hass: HomeAssistant,
    mock_vegehub: MagicMock,
    side_effect: Exception,
    expected_error: str,
) -> None:
    """Test the user flow with a timeout."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    mock_vegehub.setup.side_effect = side_effect

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_IP_ADDRESS: TEST_IP}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert "errors" in result
    assert result["errors"] == {"base": expected_error}

    mock_vegehub.setup.side_effect = None  # Clear the error

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_IP_ADDRESS: TEST_IP}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == TEST_IP
    assert result["data"][CONF_IP_ADDRESS] == TEST_IP
    assert result["data"][CONF_MAC] == TEST_SIMPLE_MAC