async def test_user_invalid_auth(
    hass: HomeAssistant, mock_smlight_client: MagicMock, mock_setup_entry: AsyncMock
) -> None:
    """Test we handle invalid auth."""
    mock_smlight_client.check_auth_needed.return_value = True
    mock_smlight_client.authenticate.side_effect = SmlightAuthError

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_HOST: MOCK_HOST,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "auth"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "test",
            CONF_PASSWORD: "bad",
        },
    )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] == {"base": "invalid_auth"}
    assert result2["step_id"] == "auth"

    mock_smlight_client.authenticate.side_effect = None

    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "test",
            CONF_PASSWORD: "good",
        },
    )

    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["title"] == "SLZB-06p7"
    assert result3["data"] == {
        CONF_HOST: MOCK_HOST,
        CONF_USERNAME: "test",
        CONF_PASSWORD: "good",
    }

    assert len(mock_setup_entry.mock_calls) == 1
    assert len(mock_smlight_client.get_info.mock_calls) == 2