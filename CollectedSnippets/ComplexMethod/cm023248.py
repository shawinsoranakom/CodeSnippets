async def test_usb_discovery_addon_not_running(
    hass: HomeAssistant,
    addon_options: dict[str, Any],
    mock_usb_serial_by_id: MagicMock,
    set_addon_options: AsyncMock,
    start_addon: AsyncMock,
) -> None:
    """Test usb discovery when add-on is installed but not running."""
    addon_options["device"] = "/dev/incorrect_device"

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USB},
        data=USB_DISCOVERY_INFO,
    )

    assert mock_usb_serial_by_id.call_count == 2
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "installation_type"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "intent_custom"}
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

    data_schema = result["data_schema"]
    assert data_schema is not None
    assert data_schema({}) == {
        "s0_legacy_key": "",
        "s2_access_control_key": "",
        "s2_authenticated_key": "",
        "s2_unauthenticated_key": "",
        "lr_s2_access_control_key": "",
        "lr_s2_authenticated_key": "",
    }

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "s0_legacy_key": "new123",
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
                "device": USB_DISCOVERY_INFO.device,
                "s0_legacy_key": "new123",
                "s2_access_control_key": "new456",
                "s2_authenticated_key": "new789",
                "s2_unauthenticated_key": "new987",
                "lr_s2_access_control_key": "new654",
                "lr_s2_authenticated_key": "new321",
            }
        ),
    )

    assert result["type"] is FlowResultType.SHOW_PROGRESS
    assert result["step_id"] == "start_addon"

    with (
        patch(
            "homeassistant.components.zwave_js.async_setup", return_value=True
        ) as mock_setup,
        patch(
            "homeassistant.components.zwave_js.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        await hass.async_block_till_done()
        result = await hass.config_entries.flow.async_configure(result["flow_id"])
        await hass.async_block_till_done()

    assert start_addon.call_args == call("core_zwave_js")

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == TITLE
    assert result["data"] == {
        "url": "ws://host1:3001",
        "usb_path": USB_DISCOVERY_INFO.device,
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