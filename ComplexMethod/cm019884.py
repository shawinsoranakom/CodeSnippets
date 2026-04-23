async def test_ssdp_auth_invalid_credentials(
    hass: HomeAssistant, mock_victron_hub: MagicMock
) -> None:
    """Test SSDP auth flow with invalid credentials."""
    mock_victron_hub.return_value.connect.side_effect = AuthenticationError(
        "Authentication required"
    )

    discovery_info = SsdpServiceInfo(
        ssdp_usn="mock_usn",
        ssdp_st="upnp:rootdevice",
        ssdp_location="http://192.168.1.100:80/",
        upnp={
            "serialNumber": MOCK_SERIAL,
            "X_VrmPortalId": MOCK_INSTALLATION_ID,
            "modelName": MOCK_MODEL,
            "friendlyName": MOCK_FRIENDLY_NAME,
            "X_MqttOnLan": "1",
            "manufacturer": "Victron Energy",
        },
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_SSDP},
        data=discovery_info,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "ssdp_auth"

    # Test with wrong credentials
    mock_victron_hub.return_value.connect.side_effect = AuthenticationError(
        "Invalid credentials"
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_USERNAME: "wrong-user",
            CONF_PASSWORD: "wrong-password",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}

    # Retry with correct credentials
    mock_victron_hub.return_value.connect.side_effect = None
    mock_victron_hub.return_value.installation_id = MOCK_INSTALLATION_ID

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_USERNAME: "test-user",
            CONF_PASSWORD: "test-password",
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].unique_id == MOCK_INSTALLATION_ID
    assert_entry_title(result)
    assert result["data"] == {
        CONF_HOST: MOCK_HOST,
        CONF_PORT: DEFAULT_PORT,
        CONF_SERIAL: MOCK_SERIAL,
        CONF_INSTALLATION_ID: MOCK_INSTALLATION_ID,
        CONF_USERNAME: "test-user",
        CONF_PASSWORD: "test-password",
        CONF_SSL: False,
    }