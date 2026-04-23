async def test_esphome_discovery_intent_recommended(
    hass: HomeAssistant,
    set_addon_options: AsyncMock,
    addon_options: dict,
    stop_addon: AsyncMock,
) -> None:
    """Test ESPHome discovery success path."""
    addon_options.update(
        {
            CONF_ADDON_DEVICE: "/dev/ttyUSB0",
            CONF_ADDON_SOCKET: None,
            "s0_legacy_key": "new123",
            "s2_access_control_key": "new456",
            "s2_authenticated_key": "new789",
            "s2_unauthenticated_key": "new987",
            "lr_s2_access_control_key": "new654",
            "lr_s2_authenticated_key": "new321",
        }
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ESPHOME},
        data=ESPHOME_DISCOVERY_INFO,
    )

    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "installation_type"
    assert result["menu_options"] == ["intent_recommended", "intent_custom"]

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
            result["flow_id"], {"next_step_id": "intent_recommended"}
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == TITLE
    assert result["result"].unique_id == str(ESPHOME_DISCOVERY_INFO.zwave_home_id)
    assert result["data"] == {
        "url": "ws://host1:3001",
        "usb_path": None,
        "socket_path": "esphome://192.168.1.100:6053",
        "s0_legacy_key": "new123",
        "s2_access_control_key": "new456",
        "s2_authenticated_key": "new789",
        "s2_unauthenticated_key": "new987",
        "lr_s2_access_control_key": "new654",
        "lr_s2_authenticated_key": "new321",
        "use_addon": True,
        "integration_created_addon": False,
    }
    assert set_addon_options.call_args == call(
        "core_zwave_js",
        AddonsOptions(
            config={
                "socket": "esphome://192.168.1.100:6053",
                "s0_legacy_key": "new123",
                "s2_access_control_key": "new456",
                "s2_authenticated_key": "new789",
                "s2_unauthenticated_key": "new987",
                "lr_s2_access_control_key": "new654",
                "lr_s2_authenticated_key": "new321",
            }
        ),
    )
    assert stop_addon.call_count == 1
    assert stop_addon.call_args == call("core_zwave_js")
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1