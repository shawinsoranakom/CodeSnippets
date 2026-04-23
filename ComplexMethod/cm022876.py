async def test_form_no_nodes_exception(
    hass: HomeAssistant,
    mock_proxmox_client: MagicMock,
) -> None:
    """Test we handle no nodes found exception."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    mock_proxmox_client.nodes.get.side_effect = ResourceException(
        "404", "status_message", "content"
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_USER_STEP
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user_auth"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_USER_AUTH_STEP_PASSWORD
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "no_nodes_found"}

    mock_proxmox_client.nodes.get.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_USER_AUTH_STEP_PASSWORD
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY