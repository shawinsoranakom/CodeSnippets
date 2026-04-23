async def test_reconfigure_not_successful(hass: HomeAssistant) -> None:
    """Test starting a reconfigure flow but no connection found."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="10.10.2.3",
        unique_id="aa:bb:cc:dd:ee:ff",
        data={
            CONF_HOST: "10.10.2.3",
            CONF_USERNAME: "fake_username",
            CONF_PASSWORD: "fake_password",
        },
    )
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    with patch(
        "homeassistant.components.nam.NettigoAirMonitor.async_get_mac_address",
        side_effect=ApiError("API Error"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: "10.10.10.10"},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    assert result["errors"] == {"base": "cannot_connect"}

    with patch(
        "homeassistant.components.nam.NettigoAirMonitor.async_get_mac_address",
        return_value="aa:bb:cc:dd:ee:ff",
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: "10.10.10.10"},
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data == {
        CONF_HOST: "10.10.10.10",
        CONF_USERNAME: "fake_username",
        CONF_PASSWORD: "fake_password",
    }