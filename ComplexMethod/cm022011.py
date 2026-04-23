async def test_import_no_host_user_finish(hass: HomeAssistant, mock_panel) -> None:
    """Test importing a panel with no host info."""
    mock_panel.get_status.return_value = {
        "mac": "aa:bb:cc:dd:ee:ff",
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
            "id": "aabbccddeeff",
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "import_confirm"
    assert result["description_placeholders"]["id"] == "aabbccddeeff"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    # confirm user is prompted to enter host
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"host": "1.1.1.1", "port": 1234}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm"
    assert result["description_placeholders"] == {
        "model": "Konnected Alarm Panel Pro",
        "id": "aabbccddeeff",
        "host": "1.1.1.1",
        "port": 1234,
    }

    # final confirmation
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY