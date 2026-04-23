async def test_addon_rf_region_new_network(
    hass: HomeAssistant,
    setup_entry: AsyncMock,
    set_addon_options: AsyncMock,
    start_addon: AsyncMock,
) -> None:
    """Test RF region selection for new network when country is None."""
    device = "/test"
    hass.config.country = None

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "installation_type"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "intent_recommended"}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "usb_path": device,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "rf_region"

    # Check that all expected RF regions are available

    data_schema = result["data_schema"]
    assert data_schema is not None
    schema = data_schema.schema
    rf_region_field = schema["rf_region"]
    selector_options = rf_region_field.config["options"]

    expected_regions = [
        "Australia/New Zealand",
        "China",
        "Europe",
        "Hong Kong",
        "India",
        "Israel",
        "Japan",
        "Korea",
        "Russia",
        "USA",
    ]

    assert selector_options == expected_regions

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"rf_region": "Europe"}
    )

    assert result["type"] is FlowResultType.SHOW_PROGRESS
    assert result["step_id"] == "start_addon"

    # Verify RF region was set in addon config
    assert set_addon_options.call_count == 1
    assert set_addon_options.call_args == call(
        "core_zwave_js",
        AddonsOptions(
            config={
                "device": device,
                "s0_legacy_key": "",
                "s2_access_control_key": "",
                "s2_authenticated_key": "",
                "s2_unauthenticated_key": "",
                "lr_s2_access_control_key": "",
                "lr_s2_authenticated_key": "",
                "rf_region": "Europe",
            }
        ),
    )

    await hass.async_block_till_done()
    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert start_addon.call_count == 1
    assert start_addon.call_args == call("core_zwave_js")
    assert setup_entry.call_count == 1

    # avoid unload entry in teardown
    entry = result["result"]
    await hass.config_entries.async_unload(entry.entry_id)
    assert entry.state is config_entries.ConfigEntryState.NOT_LOADED