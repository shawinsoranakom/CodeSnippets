async def test_reconfigure_addon_running_server_info_failure(
    hass: HomeAssistant,
    client: MagicMock,
    integration: MockConfigEntry,
    addon_options: dict[str, Any],
    set_addon_options: AsyncMock,
) -> None:
    """Test reconfigure flow and add-on already running with server info failure."""
    old_addon_options = {
        "device": "/test",
        "network_key": "abc123",
        "s0_legacy_key": "abc123",
        "s2_access_control_key": "old456",
        "s2_authenticated_key": "old789",
        "s2_unauthenticated_key": "old987",
        "lr_s2_access_control_key": "old654",
        "lr_s2_authenticated_key": "old321",
    }
    new_addon_options = {
        "usb_path": "/test",
        "s0_legacy_key": "abc123",
        "s2_access_control_key": "old456",
        "s2_authenticated_key": "old789",
        "s2_unauthenticated_key": "old987",
        "lr_s2_access_control_key": "old654",
        "lr_s2_authenticated_key": "old321",
    }
    addon_options.update(old_addon_options)
    entry = integration
    hass.config_entries.async_update_entry(entry, unique_id="1234")

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

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "configure_addon_reconfigure"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], new_addon_options
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "cannot_connect"
    assert entry.data["url"] == "ws://test.org"
    assert set_addon_options.call_count == 0
    assert client.connect.call_count == 2
    assert client.disconnect.call_count == 1