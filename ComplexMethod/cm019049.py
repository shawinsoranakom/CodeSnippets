async def test_zeroconf_with_auth(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test that the zeroconf step with auth works."""
    with patch(
        "homeassistant.components.nam.NettigoAirMonitor.async_get_mac_address",
        side_effect=AuthFailedError("Auth Error"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            data=DISCOVERY_INFO,
            context={"source": SOURCE_ZEROCONF},
        )
        context = next(
            flow["context"]
            for flow in hass.config_entries.flow.async_progress()
            if flow["flow_id"] == result["flow_id"]
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "credentials"
    assert result["errors"] == {}
    assert context["title_placeholders"]["host"] == "10.10.2.3"

    with patch(
        "homeassistant.components.nam.NettigoAirMonitor.async_get_mac_address",
        return_value="aa:bb:cc:dd:ee:ff",
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            VALID_AUTH,
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "10.10.2.3"
    assert result["data"]["host"] == "10.10.2.3"
    assert result["data"]["username"] == "fake_username"
    assert result["data"]["password"] == "fake_password"
    assert len(mock_setup_entry.mock_calls) == 1