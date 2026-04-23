async def test_user_adds_full_device(hass: HomeAssistant) -> None:
    """Test adding device with all services."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"device_input": "MRP Device"},
    )
    assert result2["type"] is FlowResultType.FORM
    assert result2["description_placeholders"] == {
        "name": "MRP Device",
        "type": "Unknown",
    }

    result3 = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result3["type"] is FlowResultType.FORM
    assert result3["description_placeholders"] == {"protocol": "MRP"}

    result4 = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"pin": 1111}
    )
    assert result4["type"] is FlowResultType.FORM
    assert result4["description_placeholders"] == {"protocol": "DMAP", "pin": "1111"}

    result5 = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result5["type"] is FlowResultType.FORM
    assert result5["description_placeholders"] == {"protocol": "AirPlay"}

    result6 = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"pin": 1234}
    )
    assert result6["type"] is FlowResultType.CREATE_ENTRY
    assert result6["data"] == {
        "address": "127.0.0.1",
        "credentials": {
            Protocol.DMAP.value: "dmap_creds",
            Protocol.MRP.value: "mrp_creds",
            Protocol.AirPlay.value: "airplay_creds",
        },
        "identifiers": ["mrpid", "dmapid", "airplayid"],
        "name": "MRP Device",
    }