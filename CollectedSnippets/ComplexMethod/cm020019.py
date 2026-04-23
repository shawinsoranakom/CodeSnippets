async def test_form_reauth_with_new_account(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """Test reauthentication with new account."""

    result = await config_entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None

    with (
        patch(
            "homeassistant.components.rympro.config_flow.RymPro.login",
            return_value="test-token",
        ),
        patch(
            "homeassistant.components.rympro.config_flow.RymPro.account_info",
            return_value={"accountNumber": "new-account-number"},
        ),
        patch(
            "homeassistant.components.rympro.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_EMAIL: TEST_DATA[CONF_EMAIL],
                CONF_PASSWORD: TEST_DATA[CONF_PASSWORD],
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "reauth_successful"
    assert config_entry.data[CONF_UNIQUE_ID] == "new-account-number"
    assert config_entry.unique_id == "new-account-number"
    assert len(mock_setup_entry.mock_calls) == 1