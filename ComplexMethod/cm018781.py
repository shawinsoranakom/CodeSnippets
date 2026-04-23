async def test_zeroconf_json_api_disabled_stale_mdns(
    hass: HomeAssistant, mock_nrgkick_api: AsyncMock
) -> None:
    """Test zeroconf discovery when JSON API is disabled."""
    mock_nrgkick_api.test_connection.side_effect = NRGkickAPIDisabledError

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZEROCONF_DISCOVERY_INFO,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "zeroconf_enable_json_api"
    assert result["description_placeholders"] == {
        "name": "NRGkick Test",
        "device_ip": "192.168.1.101",
    }

    mock_nrgkick_api.test_connection.side_effect = None

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "NRGkick Test"
    assert result["data"] == {CONF_HOST: "192.168.1.101"}
    assert result["result"].unique_id == "TEST123456"