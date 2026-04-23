async def test_user_flow_auth(
    hass: HomeAssistant, mock_smlight_client: MagicMock, mock_setup_entry: AsyncMock
) -> None:
    """Test the full manual user flow with authentication."""

    mock_smlight_client.check_auth_needed.return_value = True
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: MOCK_HOSTNAME,
        },
    )
    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "auth"

    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: MOCK_USERNAME,
            CONF_PASSWORD: MOCK_PASSWORD,
        },
    )
    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["title"] == "SLZB-06p7"
    assert result3["data"] == {
        CONF_USERNAME: MOCK_USERNAME,
        CONF_PASSWORD: MOCK_PASSWORD,
        CONF_HOST: MOCK_HOSTNAME,
    }
    assert result3["context"]["unique_id"] == "aa:bb:cc:dd:ee:ff"
    assert len(mock_setup_entry.mock_calls) == 1