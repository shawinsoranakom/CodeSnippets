async def test_form_exceptions(
    hass: HomeAssistant,
    mock_portainer_client: AsyncMock,
    exception: Exception,
    reason: str,
) -> None:
    """Test we handle all exceptions."""
    mock_portainer_client.portainer_system_status.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_USER_SETUP,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": reason}

    mock_portainer_client.portainer_system_status.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_USER_SETUP,
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "https://127.0.0.1:9000/"
    assert result["data"] == MOCK_TEST_CONFIG