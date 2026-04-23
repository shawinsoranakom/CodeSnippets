async def test_option_flow(hass: HomeAssistant, mock_panel) -> None:
    """Test config flow options."""
    device_config = config_flow.CONFIG_ENTRY_SCHEMA(
        {
            "host": "1.2.3.4",
            "port": 1234,
            "id": "112233445566",
            "model": "Konnected",
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
            "out": "Switchable Output",
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "options_binary"
    assert result["description_placeholders"] == {
        "zone": "Zone 2",
    }

    # zone 2
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={"type": "door"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "options_binary"
    assert result["description_placeholders"] == {
        "zone": "Zone 6",
    }

    # zone 6
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"type": "window", "name": "winder", "inverse": True},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "options_digital"
    assert result["description_placeholders"] == {
        "zone": "Zone 3",
    }

    # zone 3
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={"type": "dht"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "options_switch"
    assert result["description_placeholders"] == {
        "zone": "Zone 4",
        "state": "1",
    }

    # zone 4
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "options_switch"
    assert result["description_placeholders"] == {
        "zone": "OUT",
        "state": "1",
    }

    # zone out
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "name": "switcher",
            "activation": "low",
            "momentary": 50,
            "pause": 100,
            "repeat": 4,
            "more_states": "Yes",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "options_switch"
    assert result["description_placeholders"] == {
        "zone": "OUT",
        "state": "2",
    }

    # zone out - state 2
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "name": "alarm",
            "activation": "low",
            "momentary": 100,
            "pause": 100,
            "repeat": -1,
            "more_states": "No",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "options_misc"
    # make sure we enforce url format
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "discovery": False,
            "blink": True,
            "override_api_host": True,
            "api_host": "badhosturl",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "options_misc"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "discovery": False,
            "blink": True,
            "override_api_host": True,
            "api_host": "http://overridehost:1111",
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "io": {
            "2": "Binary Sensor",
            "3": "Digital Sensor",
            "4": "Switchable Output",
            "6": "Binary Sensor",
            "out": "Switchable Output",
        },
        "discovery": False,
        "blink": True,
        "api_host": "http://overridehost:1111",
        "binary_sensors": [
            {"zone": "2", "type": "door", "inverse": False},
            {"zone": "6", "type": "window", "name": "winder", "inverse": True},
        ],
        "sensors": [{"zone": "3", "type": "dht", "poll_interval": 3}],
        "switches": [
            {"activation": "high", "zone": "4"},
            {
                "zone": "out",
                "name": "switcher",
                "activation": "low",
                "momentary": 50,
                "pause": 100,
                "repeat": 4,
            },
            {
                "zone": "out",
                "name": "alarm",
                "activation": "low",
                "momentary": 100,
                "pause": 100,
                "repeat": -1,
            },
        ],
    }