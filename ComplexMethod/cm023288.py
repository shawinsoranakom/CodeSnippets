async def test_addon_skip_rf_region(
    hass: HomeAssistant,
    setup_entry: AsyncMock,
    addon_options: dict[str, Any],
    set_addon_options: AsyncMock,
    start_addon: AsyncMock,
    country: str | None,
    rf_region: str,
) -> None:
    """Test RF region selection is skipped if not needed."""
    device = "/test"
    addon_options["rf_region"] = rf_region
    hass.config.country = country

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
                "rf_region": rf_region,
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