async def test_form_with_invalid_totp(
    recorder_mock: Recorder, hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test we handle an invalid TOTP secret."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"utility": "Consolidated Edison (ConEd)"},
    )
    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "credentials"

    # Enter invalid credentials
    with patch(
        "homeassistant.components.opower.config_flow.Opower.async_login",
        side_effect=InvalidAuth,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "test-username",
                "password": "test-password",
                "totp_secret": "bad-totp",
            },
        )

    assert result3["type"] is FlowResultType.FORM
    assert result3["errors"] == {"base": "invalid_auth"}
    assert result3["step_id"] == "credentials"

    # Enter valid credentials
    with patch(
        "homeassistant.components.opower.config_flow.Opower.async_login",
    ) as mock_login:
        result4 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "test-username",
                "password": "updated-password",
                "totp_secret": "good-totp",
            },
        )

    assert result4["type"] is FlowResultType.CREATE_ENTRY
    assert result4["title"] == "Consolidated Edison (ConEd) (test-username)"
    assert result4["data"] == {
        "utility": "Consolidated Edison (ConEd)",
        "username": "test-username",
        "password": "updated-password",
        "totp_secret": "good-totp",
    }
    assert len(mock_setup_entry.mock_calls) == 1
    assert mock_login.call_count == 1