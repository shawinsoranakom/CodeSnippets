async def test_no_update_incorrect_udn_not_matching_mac_from_dhcp(
    hass: HomeAssistant, rest_api: Mock, mock_setup_entry: AsyncMock
) -> None:
    """Test that DHCP does not update the wrong udn from ssdp via host match."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={**ENTRYDATA_WEBSOCKET, CONF_MAC: "aa:bb:ss:ss:dd:pp"},
        source=config_entries.SOURCE_SSDP,
        unique_id="0d1cef00-00dc-1000-9c80-4844f7b172de",
    )
    entry.add_to_hass(hass)

    assert entry.data[CONF_HOST] == MOCK_DHCP_DATA.ip
    assert entry.data[CONF_MAC] != dr.format_mac(
        rest_api.rest_device_info.return_value["device"]["wifiMac"]
    )
    assert entry.unique_id != _strip_uuid(rest_api.rest_device_info.return_value["id"])

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_DHCP},
        data=MOCK_DHCP_DATA,
    )
    await hass.async_block_till_done()
    assert len(mock_setup_entry.mock_calls) == 0

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm"

    # Same IP + different MAC => unique id not updated
    assert entry.unique_id == "0d1cef00-00dc-1000-9c80-4844f7b172de"