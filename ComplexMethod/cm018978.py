async def test_user_cannot_connect(
    hass: HomeAssistant, mock_smlight_client: MagicMock, mock_setup_entry: AsyncMock
) -> None:
    """Test we handle user cannot connect error."""
    mock_smlight_client.check_auth_needed.side_effect = SmlightConnectionError

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "unknown.local",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}
    assert result["step_id"] == "user"

    mock_smlight_client.check_auth_needed.side_effect = None

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: MOCK_HOST,
        },
    )

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "SLZB-06p7"

    assert len(mock_setup_entry.mock_calls) == 1
    assert len(mock_smlight_client.get_info.mock_calls) == 2