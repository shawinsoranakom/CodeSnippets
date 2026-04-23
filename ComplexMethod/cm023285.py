async def test_recommended_usb_discovery(
    hass: HomeAssistant,
    install_addon: AsyncMock,
    mock_usb_serial_by_id: MagicMock,
    set_addon_options: AsyncMock,
    start_addon: AsyncMock,
    usb_discovery_info: UsbServiceInfo,
    device: str,
    discovery_name: str,
) -> None:
    """Test usb discovery success path."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USB},
        data=usb_discovery_info,
    )

    assert mock_usb_serial_by_id.call_count == 1
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "installation_type"
    assert result["menu_options"] == ["intent_recommended", "intent_custom"]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "intent_recommended"}
    )

    assert result["type"] is FlowResultType.SHOW_PROGRESS
    assert result["step_id"] == "install_addon"

    # Make sure the flow continues when the progress task is done.
    await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert install_addon.call_args == call("core_zwave_js")

    assert result["type"] is FlowResultType.SHOW_PROGRESS
    assert result["step_id"] == "start_addon"

    assert set_addon_options.call_args == call(
        "core_zwave_js",
        AddonsOptions(
            config={
                "device": device,
                "s0_legacy_key": "",
                "s2_access_control_key": "",
                "s2_authenticated_key": "",
                "s2_unauthenticated_key": "",
                "lr_s2_access_control_key": "",
                "lr_s2_authenticated_key": "",
            }
        ),
    )

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
        "usb_path": device,
        "socket_path": None,
        "s0_legacy_key": "",
        "s2_access_control_key": "",
        "s2_authenticated_key": "",
        "s2_unauthenticated_key": "",
        "lr_s2_access_control_key": "",
        "lr_s2_authenticated_key": "",
        "use_addon": True,
        "integration_created_addon": True,
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1