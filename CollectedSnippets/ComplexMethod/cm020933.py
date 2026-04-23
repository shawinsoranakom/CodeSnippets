async def test_advanced_option_flow(
    hass: HomeAssistant, config_entry_setup: MockConfigEntry
) -> None:
    """Test advanced config flow options."""
    config_entry = config_entry_setup

    result = await hass.config_entries.options.async_init(
        config_entry.entry_id, context={"show_advanced_options": True}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "configure_entity_sources"
    assert not result["last_step"]
    assert list(result["data_schema"].schema[CONF_CLIENT_SOURCE].options.keys()) == [
        "00:00:00:00:00:01"
    ]
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_CLIENT_SOURCE: ["00:00:00:00:00:01"]},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "device_tracker"
    assert not result["last_step"]
    assert list(result["data_schema"].schema[CONF_SSID_FILTER].options.keys()) == [
        "",
        "SSID 1",
        "SSID 2",
        "SSID 2_IOT",
        "SSID 3",
        "SSID 4",
    ]
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_TRACK_CLIENTS: False,
            CONF_TRACK_WIRED_CLIENTS: False,
            CONF_TRACK_DEVICES: False,
            CONF_SSID_FILTER: ["SSID 1", "SSID 2_IOT", "SSID 3", "SSID 4"],
            CONF_DETECTION_TIME: 100,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "client_control"
    assert not result["last_step"]

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_BLOCK_CLIENT: [CLIENTS[0]["mac"]],
            CONF_DPI_RESTRICTIONS: False,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "statistics_sensors"
    assert result["last_step"]

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_ALLOW_BANDWIDTH_SENSORS: True,
            CONF_ALLOW_UPTIME_SENSORS: True,
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_CLIENT_SOURCE: ["00:00:00:00:00:01"],
        CONF_TRACK_CLIENTS: False,
        CONF_TRACK_WIRED_CLIENTS: False,
        CONF_TRACK_DEVICES: False,
        CONF_SSID_FILTER: ["SSID 1", "SSID 2_IOT", "SSID 3", "SSID 4"],
        CONF_DETECTION_TIME: 100,
        CONF_IGNORE_WIRED_BUG: False,
        CONF_DPI_RESTRICTIONS: False,
        CONF_BLOCK_CLIENT: [CLIENTS[0]["mac"]],
        CONF_ALLOW_BANDWIDTH_SENSORS: True,
        CONF_ALLOW_UPTIME_SENSORS: True,
    }