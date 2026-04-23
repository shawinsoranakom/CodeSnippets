async def test_dhcp_wireless(hass: HomeAssistant) -> None:
    """Test starting a flow from dhcp."""
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
    assert result["title"] == "TV-UE48JU6470 (UE48JU6400)"
    assert result["data"][CONF_HOST] == "10.10.12.34"
    assert result["data"][CONF_MAC] == "aa:bb:aa:aa:aa:aa"
    assert result["data"][CONF_MANUFACTURER] == "Samsung"
    assert result["data"][CONF_MODEL] == "UE48JU6400"
    assert result["data"][CONF_PORT] == 8002
    assert result["result"].unique_id == "223da676-497a-4e06-9507-5e27ec4f0fb3"