async def test_options_zone_flow(hass: HomeAssistant) -> None:
    """Test options flow for adding/deleting zones."""
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

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_ZONE_NUMBER: zone_number},
    )

    with patch(
        "homeassistant.components.alarmdecoder.async_setup_entry", return_value=True
    ):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input=zone_settings,
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options == {
        OPTIONS_ARM: DEFAULT_ARM_OPTIONS,
        OPTIONS_ZONES: {zone_number: zone_settings},
    }

    # Make sure zone can be removed...
    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"edit_selection": "Zones"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "zone_select"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_ZONE_NUMBER: zone_number},
    )

    with patch(
        "homeassistant.components.alarmdecoder.async_setup_entry", return_value=True
    ):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options == {
        OPTIONS_ARM: DEFAULT_ARM_OPTIONS,
        OPTIONS_ZONES: {},
    }