async def test_reauth(
    hass: HomeAssistant,
    config,
    config_entry: MockConfigEntry,
    connect_errors,
    connect_mock,
    pro,
    setup_airvisual_pro,
) -> None:
    """Test re-auth (including errors)."""
    result = await config_entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    # Test errors that can arise when connecting to a Pro:
    with patch.object(pro, "async_connect", connect_mock):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_PASSWORD: "new_password"}
        )
        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == connect_errors

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_PASSWORD: "new_password"}
    )

    # Allow reload to finish:
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert len(hass.config_entries.async_entries()) == 1