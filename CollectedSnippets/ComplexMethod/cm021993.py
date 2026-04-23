async def test_form_with_totp(
    recorder_mock: Recorder, hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test we can configure a utility that accepts a TOTP secret."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    # Select utility
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"utility": "Consolidated Edison (ConEd)"},
    )
    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "credentials"

    # Enter credentials
    with patch(
        "homeassistant.components.opower.config_flow.Opower.async_login",
    ) as mock_login:
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "test-username",
                "password": "test-password",
                "totp_secret": "test-totp",
            },
        )

    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["title"] == "Consolidated Edison (ConEd) (test-username)"
    assert result3["data"] == {
        "utility": "Consolidated Edison (ConEd)",
        "username": "test-username",
        "password": "test-password",
        "totp_secret": "test-totp",
    }
    assert len(mock_setup_entry.mock_calls) == 1
    assert mock_login.call_count == 1