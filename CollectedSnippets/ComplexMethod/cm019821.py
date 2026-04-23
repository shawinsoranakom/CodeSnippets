async def test_integration_discovery_success(hass: HomeAssistant) -> None:
    """Test integration discovery step success path."""
    with patch(
        "homeassistant.components.yalexs_ble.util.async_discovered_service_info",
        return_value=[YALE_ACCESS_LOCK_DISCOVERY_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_INTEGRATION_DISCOVERY},
            data={
                "name": "Front Door",
                "address": YALE_ACCESS_LOCK_DISCOVERY_INFO.address,
                "key": "2fd51b8621c6a139eaffbedcb846b60f",
                "slot": 66,
                "serial": "M1XXX012LU",
            },
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "integration_discovery_confirm"
    assert result["errors"] is None

    with patch(
        "homeassistant.components.yalexs_ble.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Front Door"
    assert result2["data"] == {
        CONF_LOCAL_NAME: YALE_ACCESS_LOCK_DISCOVERY_INFO.name,
        CONF_ADDRESS: YALE_ACCESS_LOCK_DISCOVERY_INFO.address,
        CONF_KEY: "2fd51b8621c6a139eaffbedcb846b60f",
        CONF_SLOT: 66,
    }
    assert result2["result"].unique_id == YALE_ACCESS_LOCK_DISCOVERY_INFO.address
    assert len(mock_setup_entry.mock_calls) == 1