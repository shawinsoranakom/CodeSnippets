async def test_import_ssdp_host_user_finish(hass: HomeAssistant, mock_panel) -> None:
    """Test importing a pro panel with no host info which ssdp discovers."""
    mock_panel.get_status.return_value = {
        "chipId": "somechipid",
        "mac": "11:22:33:44:55:66",
        "model": "Konnected Pro",
    }

    result = await hass.config_entries.flow.async_init(
        config_flow.DOMAIN,
        context={"source": config_entries.SOURCE_IMPORT},
        data={
            "default_options": {
                "blink": True,
                "discovery": True,
                "io": {
                    "1": "Disabled",
                    "10": "Disabled",
                    "11": "Disabled",
                    "12": "Disabled",
                    "2": "Disabled",
                    "3": "Disabled",
                    "4": "Disabled",
                    "5": "Disabled",
                    "6": "Disabled",
                    "7": "Disabled",
                    "8": "Disabled",
                    "9": "Disabled",
                    "alarm1": "Disabled",
                    "alarm2_out2": "Disabled",
                    "out": "Disabled",
                    "out1": "Disabled",
                },
            },
            "id": "somechipid",
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "import_confirm"
    assert result["description_placeholders"]["id"] == "somechipid"

    # discover the panel via ssdp
    ssdp_result = await hass.config_entries.flow.async_init(
        config_flow.DOMAIN,
        context={"source": config_entries.SOURCE_SSDP},
        data=SsdpServiceInfo(
            ssdp_usn="mock_usn",
            ssdp_st="mock_st",
            ssdp_location="http://0.0.0.0:1234/Device.xml",
            upnp={
                "manufacturer": config_flow.KONN_MANUFACTURER,
                "modelName": config_flow.KONN_MODEL_PRO,
            },
        ),
    )
    assert ssdp_result["type"] is FlowResultType.ABORT
    assert ssdp_result["reason"] == "already_in_progress"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm"
    assert result["description_placeholders"] == {
        "model": "Konnected Alarm Panel Pro",
        "id": "somechipid",
        "host": "0.0.0.0",
        "port": 1234,
    }

    # final confirmation
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY