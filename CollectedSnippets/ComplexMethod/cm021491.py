async def test_dhcp_discovery_partial_hostname(hass: HomeAssistant) -> None:
    """Test we abort flows when we have a partial hostname."""

    with patch(
        "homeassistant.components.roomba.config_flow.RoombaDiscovery", _mocked_discovery
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_DHCP},
            data=DhcpServiceInfo(
                ip=MOCK_IP,
                macaddress="aabbccddeeff",
                hostname="irobot-blid",
            ),
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "link"

    with patch(
        "homeassistant.components.roomba.config_flow.RoombaDiscovery", _mocked_discovery
    ):
        result2 = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_DHCP},
            data=DhcpServiceInfo(
                ip=MOCK_IP,
                macaddress="aabbccddeeff",
                hostname="irobot-blidthatislonger",
            ),
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "link"

    current_flows = hass.config_entries.flow.async_progress()
    assert len(current_flows) == 1
    assert current_flows[0]["flow_id"] == result2["flow_id"]

    with patch(
        "homeassistant.components.roomba.config_flow.RoombaDiscovery", _mocked_discovery
    ):
        result3 = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_DHCP},
            data=DhcpServiceInfo(
                ip=MOCK_IP,
                macaddress="aabbccddeeff",
                hostname="irobot-bl",
            ),
        )
        await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.ABORT
    assert result3["reason"] == "short_blid"

    current_flows = hass.config_entries.flow.async_progress()
    assert len(current_flows) == 1
    assert current_flows[0]["flow_id"] == result2["flow_id"]