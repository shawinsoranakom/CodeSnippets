async def test_reconfigure_not_addon_with_addon(
    hass: HomeAssistant,
    setup_entry: AsyncMock,
    unload_entry: AsyncMock,
    integration: MockConfigEntry,
    stop_addon: AsyncMock,
) -> None:
    """Test reconfigure flow opting out of add-on on Supervisor with add-on."""
    entry = integration
    hass.config_entries.async_update_entry(
        entry,
        data={**entry.data, "url": "ws://host1:3001", "use_addon": True},
        unique_id="1234",
    )

    assert entry.state is config_entries.ConfigEntryState.LOADED
    assert unload_entry.call_count == 0
    setup_entry.reset_mock()

    result = await entry.start_reconfigure_flow(hass)

    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "reconfigure"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "intent_reconfigure"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "on_supervisor_reconfigure"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"use_addon": False}
    )

    assert entry.state is config_entries.ConfigEntryState.NOT_LOADED
    assert setup_entry.call_count == 0
    assert unload_entry.call_count == 1
    assert stop_addon.call_count == 1
    assert stop_addon.call_args == call("core_zwave_js")

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "manual_reconfigure"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "url": "ws://localhost:3000",
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data["url"] == "ws://localhost:3000"
    assert entry.data["use_addon"] is False
    assert entry.data["integration_created_addon"] is False
    assert entry.state is config_entries.ConfigEntryState.LOADED
    assert setup_entry.call_count == 1
    assert unload_entry.call_count == 1

    # avoid unload entry in teardown
    await hass.config_entries.async_unload(entry.entry_id)
    assert entry.state is config_entries.ConfigEntryState.NOT_LOADED