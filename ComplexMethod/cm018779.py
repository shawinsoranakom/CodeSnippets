async def test_zeroconf_discovery_with_credentials(
    hass: HomeAssistant, mock_nrgkick_api: AsyncMock, mock_setup_entry: AsyncMock
) -> None:
    """Test zeroconf discovery flow (auth required)."""

    mock_nrgkick_api.test_connection.side_effect = NRGkickAuthenticationError

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZEROCONF_DISCOVERY_INFO,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user_auth"
    assert result["description_placeholders"] == {"device_ip": "192.168.1.101"}

    mock_nrgkick_api.test_connection.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "test_user", CONF_PASSWORD: "test_pass"},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "NRGkick Test"
    assert result["data"] == {
        CONF_HOST: "192.168.1.101",
        CONF_USERNAME: "test_user",
        CONF_PASSWORD: "test_pass",
    }
    assert result["result"].unique_id == "TEST123456"
    mock_setup_entry.assert_called_once()