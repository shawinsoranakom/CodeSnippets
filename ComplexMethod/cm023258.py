async def test_addon_running(
    hass: HomeAssistant,
    addon_options: dict[str, Any],
) -> None:
    """Test add-on already running on Supervisor."""
    addon_options["device"] = "/test"
    addon_options["s0_legacy_key"] = "new123"
    addon_options["s2_access_control_key"] = "new456"
    addon_options["s2_authenticated_key"] = "new789"
    addon_options["s2_unauthenticated_key"] = "new987"
    addon_options["lr_s2_access_control_key"] = "new654"
    addon_options["lr_s2_authenticated_key"] = "new321"

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

    with (
        patch(
            "homeassistant.components.zwave_js.async_setup", return_value=True
        ) as mock_setup,
        patch(
            "homeassistant.components.zwave_js.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"use_addon": True}
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == TITLE
    assert result["data"] == {
        "url": "ws://host1:3001",
        "usb_path": "/test",
        "socket_path": None,
        "s0_legacy_key": "new123",
        "s2_access_control_key": "new456",
        "s2_authenticated_key": "new789",
        "s2_unauthenticated_key": "new987",
        "lr_s2_access_control_key": "new654",
        "lr_s2_authenticated_key": "new321",
        "use_addon": True,
        "integration_created_addon": False,
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1