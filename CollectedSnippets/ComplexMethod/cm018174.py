async def test_reauth(hass: HomeAssistant, mock_account: Account) -> None:
    """Test reauth flow (with fail and recover)."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=CONFIG[DOMAIN],
        unique_id=ACCOUNT_USER_ID,
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    with patch(
        "homeassistant.components.litterrobot.config_flow.Account.connect",
        side_effect=LitterRobotLoginException,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_PASSWORD: CONFIG[DOMAIN][CONF_PASSWORD]},
        )

        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {"base": "invalid_auth"}

    with (
        patch(
            "homeassistant.components.litterrobot.config_flow.Account.connect",
            return_value=mock_account,
        ),
        patch(
            "homeassistant.components.litterrobot.config_flow.Account.user_id",
            new_callable=PropertyMock,
            return_value=ACCOUNT_USER_ID,
        ),
        patch(
            "homeassistant.components.litterrobot.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_PASSWORD: CONFIG[DOMAIN][CONF_PASSWORD]},
        )
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "reauth_successful"
        assert entry.unique_id == ACCOUNT_USER_ID
        assert len(mock_setup_entry.mock_calls) == 1