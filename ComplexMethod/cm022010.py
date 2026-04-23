async def test_ssdp(hass: HomeAssistant, mock_panel) -> None:
    """Test a panel being discovered."""
    mock_panel.get_status.return_value = {
        "mac": "11:22:33:44:55:66",
        "model": "Konnected",
    }

    # Test success
    result = await hass.config_entries.flow.async_init(
        config_flow.DOMAIN,
        context={"source": config_entries.SOURCE_SSDP},
        data=SsdpServiceInfo(
            ssdp_usn="mock_usn",
            ssdp_st="mock_st",
            ssdp_location="http://1.2.3.4:1234/Device.xml",
            upnp={
                "manufacturer": config_flow.KONN_MANUFACTURER,
                "modelName": config_flow.KONN_MODEL,
            },
        ),
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm"
    assert result["description_placeholders"] == {
        "model": "Konnected Alarm Panel",
        "id": "112233445566",
        "host": "1.2.3.4",
        "port": 1234,
    }

    # Test abort if connection failed
    mock_panel.get_status.side_effect = config_flow.CannotConnect
    result = await hass.config_entries.flow.async_init(
        config_flow.DOMAIN,
        context={"source": config_entries.SOURCE_SSDP},
        data=SsdpServiceInfo(
            ssdp_usn="mock_usn",
            ssdp_st="mock_st",
            ssdp_location="http://1.2.3.4:1234/Device.xml",
            upnp={
                "manufacturer": config_flow.KONN_MANUFACTURER,
                "modelName": config_flow.KONN_MODEL,
            },
        ),
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "cannot_connect"

    # Test abort if invalid data
    mock_panel.get_status.side_effect = KeyError
    result = await hass.config_entries.flow.async_init(
        config_flow.DOMAIN,
        context={"source": config_entries.SOURCE_SSDP},
        data=SsdpServiceInfo(
            ssdp_usn="mock_usn",
            ssdp_st="mock_st",
            ssdp_location="http://1.2.3.4:1234/Device.xml",
            upnp={},
        ),
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "unknown"

    # Test abort if invalid manufacturer
    result = await hass.config_entries.flow.async_init(
        config_flow.DOMAIN,
        context={"source": config_entries.SOURCE_SSDP},
        data=SsdpServiceInfo(
            ssdp_usn="mock_usn",
            ssdp_st="mock_st",
            ssdp_location="http://1.2.3.4:1234/Device.xml",
            upnp={
                "manufacturer": "SHOULD_FAIL",
                "modelName": config_flow.KONN_MODEL,
            },
        ),
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "not_konn_panel"

    # Test abort if invalid model
    result = await hass.config_entries.flow.async_init(
        config_flow.DOMAIN,
        context={"source": config_entries.SOURCE_SSDP},
        data=SsdpServiceInfo(
            ssdp_usn="mock_usn",
            ssdp_st="mock_st",
            ssdp_location="http://1.2.3.4:1234/Device.xml",
            upnp={
                "manufacturer": config_flow.KONN_MANUFACTURER,
                "modelName": "SHOULD_FAIL",
            },
        ),
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "not_konn_panel"

    # Test abort if already configured
    config_entry = MockConfigEntry(
        domain=config_flow.DOMAIN,
        data={config_flow.CONF_HOST: "1.2.3.4", config_flow.CONF_PORT: 1234},
    )
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        config_flow.DOMAIN,
        context={"source": config_entries.SOURCE_SSDP},
        data=SsdpServiceInfo(
            ssdp_usn="mock_usn",
            ssdp_st="mock_st",
            ssdp_location="http://1.2.3.4:1234/Device.xml",
            upnp={
                "manufacturer": config_flow.KONN_MANUFACTURER,
                "modelName": config_flow.KONN_MODEL,
            },
        ),
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"