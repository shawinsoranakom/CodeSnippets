async def test_standard_config_with_multiple_fireplace(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_apis_multifp,
) -> None:
    """Test multi-fireplace user who must be very rich."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}
    assert result["step_id"] == "cloud_api"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "donJulio", CONF_PASSWORD: "Tequila0FD00m"},
    )
    # When we have multiple fireplaces we get to pick a serial
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "pick_cloud_device"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_SERIAL: "4GC295860E5837G40D9974B7FD459234"},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "ip_address": "192.168.2.109",
        "api_key": "D4C5EB28BBFF41E1FB21AFF9BFA6CD34",
        "serial": "4GC295860E5837G40D9974B7FD459234",
        "auth_cookie": "B984F21A6378560019F8A1CDE41B6782",
        "web_client_id": "FA2B1C3045601234D0AE17D72F8E975",
        "user_id": "52C3F9E8B9D3AC99F8E4D12345678901FE9A2BC7D85F7654E28BF98BCD123456",
        "username": "grumpypanda@china.cn",
        "password": "you-stole-my-pandas",
    }