async def test_full_zeroconf_flow_implementation(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test the full manual user flow from start to finish."""
    aioclient_mock.post(
        "http://192.168.1.123:80/mf",
        text=await async_load_fixture(hass, "device_info.json", DOMAIN),
        headers={"Content-Type": CONTENT_TYPE_JSON},
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("192.168.1.123"),
            ip_addresses=[ip_address("192.168.1.123")],
            hostname="example.local.",
            name="mock_name",
            port=None,
            properties={},
            type="mock_type",
        ),
    )

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1

    assert result.get("description_placeholders") == {CONF_NAME: "example"}
    assert result.get("step_id") == "zeroconf_confirm"
    assert result.get("type") is FlowResultType.FORM

    flow = hass.config_entries.flow._progress[flows[0]["flow_id"]]
    assert flow.host == "192.168.1.123"
    assert flow.name == "example"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    assert result2.get("title") == "example"
    assert result2.get("type") is FlowResultType.CREATE_ENTRY

    assert "data" in result2
    assert result2["data"][CONF_HOST] == "192.168.1.123"
    assert result2["data"][CONF_MAC] == "AA:BB:CC:DD:EE:FF"