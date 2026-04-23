async def test_reconfigure_error(
    hass: HomeAssistant, config_entry: MockConfigEntry, sabnzbd: AsyncMock
) -> None:
    """Test reconfiguring a SABnzbd entry."""
    result = await config_entry.start_reconfigure_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    # set side effect and check if error is handled
    sabnzbd.check_available.side_effect = SabnzbdApiException("Some error")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_URL: "http://10.10.10.10:8080", CONF_API_KEY: "new_key"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "cannot_connect"}

    # reset side effect and check if we can recover
    sabnzbd.check_available.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_URL: "http://10.10.10.10:8080", CONF_API_KEY: "new_key"},
    )

    assert "errors" not in result
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert config_entry.data == {
        CONF_URL: "http://10.10.10.10:8080",
        CONF_API_KEY: "new_key",
    }