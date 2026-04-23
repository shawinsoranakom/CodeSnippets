async def test_options_add_device(hass: HomeAssistant) -> None:
    """Test we can add a device."""

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "host": None,
            "port": None,
            "device": "/dev/tty123",
            "automatic_add": False,
            "devices": {},
        },
        unique_id=DOMAIN,
    )
    result = await start_options_flow(hass, entry)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "prompt_options"

    # Try with invalid event code
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"automatic_add": True, "event_code": "1234"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "prompt_options"
    assert result["errors"]
    assert result["errors"]["event_code"] == "invalid_event_code"

    # Try with valid event code
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "automatic_add": True,
            "event_code": "0b1100cd0213c7f230010f71",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "set_device_options"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY

    await hass.async_block_till_done()

    assert entry.data["automatic_add"]

    assert entry.data["devices"]["0b1100cd0213c7f230010f71"]
    assert "delay_off" not in entry.data["devices"]["0b1100cd0213c7f230010f71"]

    state = hass.states.get("binary_sensor.ac_213c7f2_48")
    assert state
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get("friendly_name") == "AC 213c7f2:48"