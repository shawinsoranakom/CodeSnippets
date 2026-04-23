async def test_form_reauth(hass: HomeAssistant) -> None:
    """Test that the reauth confirmation form is served."""
    entry = configure_integration(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    result = await entry.start_reauth_flow(hass)
    assert result["step_id"] == "reauth_confirm"
    assert result["type"] is FlowResultType.FORM

    with (
        patch(
            "homeassistant.components.devolo_home_network.async_setup_entry",
            return_value=True,
        ),
        patch(
            "homeassistant.components.devolo_home_network.config_flow.Device",
            new=MockDeviceWrongPassword,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PASSWORD: "test-wrong-password"},
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] == {CONF_BASE: "invalid_auth"}

    with (
        patch(
            "homeassistant.components.devolo_home_network.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
        patch(
            "homeassistant.components.devolo_home_network.config_flow.Device",
            new=MockDevice,
        ),
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PASSWORD: "test-right-password"},
        )
        await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.ABORT
    assert result3["reason"] == "reauth_successful"
    assert len(mock_setup_entry.mock_calls) == 1
    assert entry.data[CONF_PASSWORD] == "test-right-password"