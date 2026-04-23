async def test_addon_running_already_configured(
    hass: HomeAssistant,
    addon_options: dict[str, Any],
) -> None:
    """Test that only one unique instance is allowed when add-on is running."""
    addon_options["device"] = "/test_new"
    addon_options["s0_legacy_key"] = "new123"
    addon_options["s2_access_control_key"] = "new456"
    addon_options["s2_authenticated_key"] = "new789"
    addon_options["s2_unauthenticated_key"] = "new987"
    addon_options["lr_s2_access_control_key"] = "new654"
    addon_options["lr_s2_authenticated_key"] = "new321"

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "url": "ws://localhost:3000",
            "usb_path": "/test",
            "network_key": "old123",
            "s0_legacy_key": "old123",
            "s2_access_control_key": "old456",
            "s2_authenticated_key": "old789",
            "s2_unauthenticated_key": "old987",
            "lr_s2_access_control_key": "old654",
            "lr_s2_authenticated_key": "old321",
        },
        title=TITLE,
        unique_id=1234,  # Unique ID is purposely set to int to test migration logic
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "installation_type"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "intent_custom"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "on_supervisor"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"use_addon": True}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert entry.data["url"] == "ws://host1:3001"
    assert entry.data["usb_path"] == "/test_new"
    assert entry.data["socket_path"] is None
    assert entry.data["s0_legacy_key"] == "new123"
    assert entry.data["s2_access_control_key"] == "new456"
    assert entry.data["s2_authenticated_key"] == "new789"
    assert entry.data["s2_unauthenticated_key"] == "new987"
    assert entry.data["lr_s2_access_control_key"] == "new654"
    assert entry.data["lr_s2_authenticated_key"] == "new321"