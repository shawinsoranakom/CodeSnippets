async def test_options_zone_flow_validation(hass: HomeAssistant) -> None:
    """Test input validation for zone options flow."""
    zone_number = "2"
    zone_settings = {
        CONF_ZONE_NAME: "Front Entry",
        CONF_ZONE_TYPE: BinarySensorDeviceClass.WINDOW,
    }
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"edit_selection": "Zones"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "zone_select"

    # Zone Number must be int
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_ZONE_NUMBER: "asd"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "zone_select"
    assert result["errors"] == {CONF_ZONE_NUMBER: "int"}

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_ZONE_NUMBER: zone_number},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "zone_details"

    # CONF_RELAY_ADDR & CONF_RELAY_CHAN are inclusive
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={**zone_settings, CONF_RELAY_ADDR: "1"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "zone_details"
    assert result["errors"] == {"base": "relay_inclusive"}

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={**zone_settings, CONF_RELAY_CHAN: "1"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "zone_details"
    assert result["errors"] == {"base": "relay_inclusive"}

    # CONF_RELAY_ADDR, CONF_RELAY_CHAN must be int
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={**zone_settings, CONF_RELAY_ADDR: "abc", CONF_RELAY_CHAN: "abc"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "zone_details"
    assert result["errors"] == {
        CONF_RELAY_ADDR: "int",
        CONF_RELAY_CHAN: "int",
    }

    # CONF_ZONE_LOOP depends on CONF_ZONE_RFID
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={**zone_settings, CONF_ZONE_LOOP: "1"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "zone_details"
    assert result["errors"] == {CONF_ZONE_LOOP: "loop_rfid"}

    # CONF_ZONE_LOOP must be int
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={**zone_settings, CONF_ZONE_RFID: "rfid123", CONF_ZONE_LOOP: "ab"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "zone_details"
    assert result["errors"] == {CONF_ZONE_LOOP: "int"}

    # CONF_ZONE_LOOP must be between [1,4]
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={**zone_settings, CONF_ZONE_RFID: "rfid123", CONF_ZONE_LOOP: "5"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "zone_details"
    assert result["errors"] == {CONF_ZONE_LOOP: "loop_range"}

    # All valid settings
    with patch(
        "homeassistant.components.alarmdecoder.async_setup_entry", return_value=True
    ):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                **zone_settings,
                CONF_ZONE_RFID: "rfid123",
                CONF_ZONE_LOOP: "2",
                CONF_RELAY_ADDR: "12",
                CONF_RELAY_CHAN: "1",
            },
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options == {
        OPTIONS_ARM: DEFAULT_ARM_OPTIONS,
        OPTIONS_ZONES: {
            zone_number: {
                **zone_settings,
                CONF_ZONE_RFID: "rfid123",
                CONF_ZONE_LOOP: 2,
                CONF_RELAY_ADDR: 12,
                CONF_RELAY_CHAN: 1,
            }
        },
    }