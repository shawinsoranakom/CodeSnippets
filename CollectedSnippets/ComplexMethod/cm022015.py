async def test_option_flow_import(hass: HomeAssistant, mock_panel) -> None:
    """Test config flow options imported from configuration.yaml."""
    device_options = config_flow.OPTIONS_SCHEMA(
        {
            "io": {
                "1": "Binary Sensor",
                "2": "Digital Sensor",
                "3": "Switchable Output",
            },
            "binary_sensors": [
                {"zone": "1", "type": "window", "name": "winder", "inverse": True},
            ],
            "sensors": [{"zone": "2", "type": "ds18b20", "name": "temper"}],
            "switches": [
                {
                    "zone": "3",
                    "name": "switcher",
                    "activation": "low",
                    "momentary": 50,
                    "pause": 100,
                    "repeat": 4,
                },
                {
                    "zone": "3",
                    "name": "alarm",
                    "activation": "low",
                    "momentary": 100,
                    "pause": 100,
                    "repeat": -1,
                },
            ],
        }
    )

    device_config = config_flow.CONFIG_ENTRY_SCHEMA(
        {
            "host": "1.2.3.4",
            "port": 1234,
            "id": "112233445566",
            "model": "Konnected Pro",
            "access_token": "11223344556677889900",
            "default_options": device_options,
        }
    )

    entry = MockConfigEntry(
        domain="konnected", data=device_config, unique_id="112233445566"
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(
        entry.entry_id, context={"source": "test"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "options_io"

    # confirm the defaults are set based on current config - we"ll spot check this throughout
    schema = result["data_schema"]({})
    assert schema["1"] == "Binary Sensor"
    assert schema["2"] == "Digital Sensor"
    assert schema["3"] == "Switchable Output"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "1": "Binary Sensor",
            "2": "Digital Sensor",
            "3": "Switchable Output",
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "options_io_ext"
    schema = result["data_schema"]({})
    assert schema["8"] == "Disabled"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "options_binary"

    # zone 1
    schema = result["data_schema"]({})
    assert schema["type"] == "window"
    assert schema["name"] == "winder"
    assert schema["inverse"] is True
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={"type": "door"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "options_digital"

    # zone 2
    schema = result["data_schema"]({})
    assert schema["type"] == "ds18b20"
    assert schema["name"] == "temper"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"type": "dht"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "options_switch"

    # zone 3
    schema = result["data_schema"]({})
    assert schema["name"] == "switcher"
    assert schema["activation"] == "low"
    assert schema["momentary"] == 50
    assert schema["pause"] == 100
    assert schema["repeat"] == 4
    assert schema["more_states"] == "Yes"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={"activation": "high", "more_states": "No"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "options_misc"

    schema = result["data_schema"]({})
    assert schema["blink"] is True
    assert schema["discovery"] is True
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"discovery": True, "blink": False, "override_api_host": False},
    )

    # verify the updated fields
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "io": {"1": "Binary Sensor", "2": "Digital Sensor", "3": "Switchable Output"},
        "discovery": True,
        "blink": False,
        "api_host": "",
        "binary_sensors": [
            {"zone": "1", "type": "door", "inverse": True, "name": "winder"},
        ],
        "sensors": [
            {"zone": "2", "type": "dht", "poll_interval": 3, "name": "temper"},
        ],
        "switches": [
            {
                "zone": "3",
                "name": "switcher",
                "activation": "high",
                "momentary": 50,
                "pause": 100,
                "repeat": 4,
            },
        ],
    }