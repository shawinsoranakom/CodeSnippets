async def test_standard_config_with_single_fireplace_and_bad_credentials(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_apis_single_fp,
) -> None:
    """Test bad credentials on a login."""
    _mock_local_interface, mock_cloud_interface, _mock_fp = mock_apis_single_fp
    # Set login error
    mock_cloud_interface.login_with_credentials.side_effect = LoginError

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

    # Erase the error
    mock_cloud_interface.login_with_credentials.side_effect = None

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "api_error"}
    assert result["step_id"] == "cloud_api"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "donJulio", CONF_PASSWORD: "Tequila0FD00m"},
    )
    # For a single fireplace we just create it
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "ip_address": "192.168.2.108",
        "api_key": "B5C4DA27AAEF31D1FB21AFF9BFA6BCD2",
        "serial": "3FB284769E4736F30C8973A7ED358123",
        "auth_cookie": "B984F21A6378560019F8A1CDE41B6782",
        "web_client_id": "FA2B1C3045601234D0AE17D72F8E975",
        "user_id": "52C3F9E8B9D3AC99F8E4D12345678901FE9A2BC7D85F7654E28BF98BCD123456",
        "username": "grumpypanda@china.cn",
        "password": "you-stole-my-pandas",
    }