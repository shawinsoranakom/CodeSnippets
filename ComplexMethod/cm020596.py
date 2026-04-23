async def test_dhcp_wired(hass: HomeAssistant, rest_api: Mock) -> None:
    """Test starting a flow from dhcp."""
    # Even though it is named "wifiMac", it matches the mac of the wired connection
    rest_api.rest_device_info.return_value = await async_load_json_object_fixture(
        hass, "device_info_UE43LS003.json", DOMAIN
    )
    # confirm to add the entry
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_DHCP},
        data=MOCK_DHCP_DATA,
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm"

    # entry was added
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input="whatever"
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Samsung Frame (43) (UE43LS003)"
    assert result["data"][CONF_HOST] == "10.10.12.34"
    assert result["data"][CONF_MAC] == "aa:ee:tt:hh:ee:rr"
    assert result["data"][CONF_MANUFACTURER] == "Samsung"
    assert result["data"][CONF_MODEL] == "UE43LS003"
    assert result["data"][CONF_PORT] == 8002
    assert result["result"].unique_id == "be9554b9-c9fb-41f4-8920-22da015376a4"