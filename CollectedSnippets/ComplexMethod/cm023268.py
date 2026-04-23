async def test_reconfigure_not_addon(
    hass: HomeAssistant,
    client: MagicMock,
    integration: MockConfigEntry,
) -> None:
    """Test reconfigure flow and opting out of add-on on Supervisor."""
    entry = integration
    hass.config_entries.async_update_entry(entry, unique_id="1234")

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
        result["flow_id"], {"use_addon": False}
    )

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
    assert client.connect.call_count == 2
    assert client.disconnect.call_count == 1