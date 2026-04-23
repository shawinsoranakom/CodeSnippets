async def test_zeroconf(hass: HomeAssistant) -> None:
    """Test zeroconf discovery."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("127.0.0.1"),
            ip_addresses=[ip_address("127.0.0.1")],
            hostname="mock_hostname",
            name="mock_name",
            port=3000,
            type="_zwave-js-server._tcp.local.",
            properties={"homeId": "1234"},
        ),
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "zeroconf_confirm"

    # Verify discovery notification shows home ID with network location
    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    flow = flows[0]
    assert flow["context"]["title_placeholders"]["host"] == "127.0.0.1"
    assert flow["context"]["title_placeholders"]["port"] == "3000"
    assert flow["context"]["title_placeholders"]["home_id"] == "0x000004d2"  # 1234

    with (
        patch(
            "homeassistant.components.zwave_js.async_setup", return_value=True
        ) as mock_setup,
        patch(
            "homeassistant.components.zwave_js.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == TITLE
    assert result["data"] == {
        "url": "ws://127.0.0.1:3000",
        "usb_path": None,
        "socket_path": None,
        "s0_legacy_key": None,
        "s2_access_control_key": None,
        "s2_authenticated_key": None,
        "s2_unauthenticated_key": None,
        "lr_s2_access_control_key": None,
        "lr_s2_authenticated_key": None,
        "use_addon": False,
        "integration_created_addon": False,
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1