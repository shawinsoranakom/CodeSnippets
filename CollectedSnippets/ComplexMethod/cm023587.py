async def test_create_entry_without_auth(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_lhm_client: AsyncMock,
) -> None:
    """Test that a complete config entry is created."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=VALID_CONFIG
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].unique_id is None

    created_config_entry = result["result"]
    assert (
        created_config_entry.title
        == f"GAMING-PC ({VALID_CONFIG[CONF_HOST]}:{VALID_CONFIG[CONF_PORT]})"
    )
    assert created_config_entry.data == VALID_CONFIG

    assert mock_setup_entry.call_count == 1