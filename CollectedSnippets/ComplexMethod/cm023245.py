async def test_manual_already_configured(hass: HomeAssistant) -> None:
    """Test that only one unique instance is allowed."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "url": "ws://localhost:3000",
            "use_addon": True,
            "integration_created_addon": True,
        },
        title=TITLE,
        unique_id="1234",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "manual"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "url": "ws://1.1.1.1:3001",
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert entry.data["url"] == "ws://1.1.1.1:3001"
    assert entry.data["use_addon"] is False
    assert entry.data["integration_created_addon"] is False