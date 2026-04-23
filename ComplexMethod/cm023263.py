async def test_addon_installed_set_options_failure(
    hass: HomeAssistant,
    set_addon_options: AsyncMock,
    start_addon: AsyncMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test all failures when add-on is installed."""
    secret = TEST_SENSITIVE_NETWORK_KEY

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

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "configure_addon_user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "usb_path": "/test",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "network_type"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "network_type": "existing",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "configure_security_keys"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "s0_legacy_key": secret,
            "s2_access_control_key": "new456",
            "s2_authenticated_key": "new789",
            "s2_unauthenticated_key": "new987",
            "lr_s2_access_control_key": "new654",
            "lr_s2_authenticated_key": "new321",
        },
    )

    assert set_addon_options.call_args == call(
        "core_zwave_js",
        AddonsOptions(
            config={
                "device": "/test",
                "s0_legacy_key": secret,
                "s2_access_control_key": "new456",
                "s2_authenticated_key": "new789",
                "s2_unauthenticated_key": "new987",
                "lr_s2_access_control_key": "new654",
                "lr_s2_authenticated_key": "new321",
            }
        ),
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "addon_set_config_failed"

    assert start_addon.call_count == 0
    assert "Failed to set the Z-Wave JS app options" in caplog.text
    assert "not a valid value for dictionary value" in caplog.text
    assert REDACTED in caplog.text
    assert secret not in caplog.text