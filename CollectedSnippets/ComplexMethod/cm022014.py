async def test_option_flow_pro(hass: HomeAssistant, mock_panel) -> None:
    """Test config flow options for pro board."""
    device_config = config_flow.CONFIG_ENTRY_SCHEMA(
        {
            "host": "1.2.3.4",
            "port": 1234,
            "id": "112233445566",
            "model": "Konnected Pro",
            "access_token": "11223344556677889900",
            "default_options": config_flow.OPTIONS_SCHEMA({config_flow.CONF_IO: {}}),
        }
    )

    device_options = config_flow.OPTIONS_SCHEMA({"io": {}})

    entry = MockConfigEntry(
        domain="konnected",
        data=device_config,
        options=device_options,
        unique_id="112233445566",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(
        entry.entry_id, context={"source": "test"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "options_io"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "1": "Disabled",
            "2": "Binary Sensor",
            "3": "Digital Sensor",
            "4": "Switchable Output",
            "5": "Disabled",
            "6": "Binary Sensor",
            "7": "Digital Sensor",
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "options_io_ext"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "8": "Switchable Output",
            "9": "Disabled",
            "10": "Binary Sensor",
            "11": "Binary Sensor",
            "12": "Disabled",
            "out1": "Switchable Output",
            "alarm1": "Switchable Output",
            "alarm2_out2": "Disabled",
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "options_binary"

    # zone 2
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={"type": "door"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "options_binary"

    # zone 6
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"type": "window", "name": "winder", "inverse": True},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "options_binary"

    # zone 10
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={"type": "door"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "options_binary"

    # zone 11
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={"type": "window"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "options_digital"

    # zone 3
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={"type": "dht"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "options_digital"

    # zone 7
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={"type": "ds18b20", "name": "temper"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "options_switch"

    # zone 4
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "options_switch"

    # zone 8
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "name": "switcher",
            "activation": "low",
            "momentary": 50,
            "pause": 100,
            "repeat": 4,
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "options_switch"

    # zone out1
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "options_switch"

    # zone alarm1
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "options_misc"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"discovery": False, "blink": True, "override_api_host": False},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "io": {
            "10": "Binary Sensor",
            "11": "Binary Sensor",
            "2": "Binary Sensor",
            "3": "Digital Sensor",
            "4": "Switchable Output",
            "6": "Binary Sensor",
            "7": "Digital Sensor",
            "8": "Switchable Output",
            "alarm1": "Switchable Output",
            "out1": "Switchable Output",
        },
        "discovery": False,
        "blink": True,
        "api_host": "",
        "binary_sensors": [
            {"zone": "2", "type": "door", "inverse": False},
            {"zone": "6", "type": "window", "name": "winder", "inverse": True},
            {"zone": "10", "type": "door", "inverse": False},
            {"zone": "11", "type": "window", "inverse": False},
        ],
        "sensors": [
            {"zone": "3", "type": "dht", "poll_interval": 3},
            {"zone": "7", "type": "ds18b20", "name": "temper", "poll_interval": 3},
        ],
        "switches": [
            {"activation": "high", "zone": "4"},
            {
                "zone": "8",
                "name": "switcher",
                "activation": "low",
                "momentary": 50,
                "pause": 100,
                "repeat": 4,
            },
            {"activation": "high", "zone": "out1"},
            {"activation": "high", "zone": "alarm1"},
        ],
    }