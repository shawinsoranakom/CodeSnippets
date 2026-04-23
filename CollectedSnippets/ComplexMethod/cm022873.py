async def test_form(
    hass: HomeAssistant,
    mock_proxmox_client: MagicMock,
    mock_user_step: dict[str, Any],
    mock_user_auth_step: dict[str, Any],
    mock_test_config: dict[str, Any],
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=mock_user_step
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user_auth"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=mock_user_auth_step
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "127.0.0.1"
    assert result["data"] == mock_test_config