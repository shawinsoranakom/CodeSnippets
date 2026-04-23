async def test_webhook_reconfigure_flow(
    hass: HomeAssistant, webhook_flow_conf: None
) -> None:
    """Test webhook reconfigure flow."""
    config_entry = MockConfigEntry(
        domain="test_single",
        data={
            "webhook_id": "12345",
            "cloudhook": False,
            "other_entry_data": "not_changed",
        },
    )
    config_entry.add_to_hass(hass)

    flow = config_entries.HANDLERS["test_single"]()
    flow.hass = hass
    flow.context = {
        "source": config_entries.SOURCE_RECONFIGURE,
        "entry_id": config_entry.entry_id,
    }

    await async_process_ha_core_config(
        hass,
        {"external_url": "https://example.com"},
    )

    result = await flow.async_step_reconfigure()
    assert result["type"] is data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    result = await flow.async_step_reconfigure(user_input={})

    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert result["description_placeholders"] == {
        "webhook_url": "https://example.com/api/webhook/12345"
    }
    assert config_entry.data["webhook_id"] == "12345"
    assert config_entry.data["cloudhook"] is False
    assert config_entry.data["other_entry_data"] == "not_changed"