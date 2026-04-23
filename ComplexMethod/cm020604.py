async def test_update_incorrect_udn_matching_mac_from_dhcp(
    hass: HomeAssistant, rest_api: Mock, mock_setup_entry: AsyncMock
) -> None:
    """Test that DHCP updates the wrong udn from ssdp via mac match."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={**ENTRYDATA_WEBSOCKET, CONF_MAC: "aa:bb:aa:aa:aa:aa"},
        source=config_entries.SOURCE_SSDP,
        unique_id="0d1cef00-00dc-1000-9c80-4844f7b172de",
    )
    entry.add_to_hass(hass)

    assert entry.data[CONF_HOST] == MOCK_DHCP_DATA.ip
    assert entry.data[CONF_MAC] == dr.format_mac(
        rest_api.rest_device_info.return_value["device"]["wifiMac"]
    )
    assert entry.unique_id != _strip_uuid(rest_api.rest_device_info.return_value["id"])

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_DHCP},
        data=MOCK_DHCP_DATA,
    )
    await hass.async_block_till_done()
    assert len(mock_setup_entry.mock_calls) == 1

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"

    # Same IP + same MAC => unique id updated
    assert entry.unique_id == "be9554b9-c9fb-41f4-8920-22da015376a4"