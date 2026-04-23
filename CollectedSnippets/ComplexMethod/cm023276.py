async def test_reconfigure_addon_not_installed(
    hass: HomeAssistant,
    client: MagicMock,
    install_addon: AsyncMock,
    integration: MockConfigEntry,
    addon_options: dict[str, Any],
    set_addon_options: AsyncMock,
    start_addon: AsyncMock,
    entry_data: dict[str, Any],
    old_addon_options: dict[str, Any],
    form_data: dict[str, Any],
    new_addon_options: dict[str, Any],
    disconnect_calls: int,
) -> None:
    """Test reconfigure flow and add-on not installed on Supervisor."""
    addon_options.update(old_addon_options)
    entry = integration
    data = {**entry.data, **entry_data}
    hass.config_entries.async_update_entry(entry, data=data, unique_id="1234")

    assert entry.data["url"] == "ws://test.org"

    assert client.connect.call_count == 1
    assert client.disconnect.call_count == 0

    result = await entry.start_reconfigure_flow(hass)

    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "reconfigure"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "intent_reconfigure"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "on_supervisor_reconfigure"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"use_addon": True}
    )

    assert result["type"] is FlowResultType.SHOW_PROGRESS
    assert result["step_id"] == "install_addon"

    # Make sure the flow continues when the progress task is done.
    await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert install_addon.call_args == call("core_zwave_js")

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "configure_addon_reconfigure"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], form_data
    )

    assert set_addon_options.call_args == call(
        "core_zwave_js", AddonsOptions(config=new_addon_options)
    )
    assert client.disconnect.call_count == disconnect_calls

    assert result["type"] is FlowResultType.SHOW_PROGRESS
    assert result["step_id"] == "start_addon"

    await hass.async_block_till_done()

    assert start_addon.call_count == 1
    assert start_addon.call_args == call("core_zwave_js")

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data["url"] == "ws://host1:3001"
    assert entry.data["usb_path"] == new_addon_options.get("device")
    assert entry.data["s0_legacy_key"] == new_addon_options["s0_legacy_key"]
    assert entry.data["use_addon"] is True
    assert entry.data["integration_created_addon"] is True
    assert client.connect.call_count == 2
    assert client.disconnect.call_count == 1