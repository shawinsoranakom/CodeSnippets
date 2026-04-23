async def test_integration_discovery_takes_precedence_over_bluetooth_uuid_address(
    hass: HomeAssistant,
) -> None:
    """Test integration discovery dismisses bluetooth discovery with a uuid address."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=LOCK_DISCOVERY_INFO_UUID_ADDRESS,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "key_slot"
    assert result["errors"] == {}
    flows = list(hass.config_entries.flow._handler_progress_index[DOMAIN])
    assert len(flows) == 1
    assert flows[0].unique_id == LOCK_DISCOVERY_INFO_UUID_ADDRESS.address
    assert flows[0].local_name == LOCK_DISCOVERY_INFO_UUID_ADDRESS.name

    with patch(
        "homeassistant.components.yalexs_ble.util.async_discovered_service_info",
        return_value=[LOCK_DISCOVERY_INFO_UUID_ADDRESS],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_INTEGRATION_DISCOVERY},
            data={
                "name": "Front Door",
                "address": "AA:BB:CC:DD:EE:FF",
                "key": "2fd51b8621c6a139eaffbedcb846b60f",
                "slot": 66,
                "serial": "M1XXX012LU",
            },
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "integration_discovery_confirm"
    assert result["errors"] is None

    # the bluetooth flow should get dismissed in favor
    # of the integration discovery flow since the integration
    # discovery flow will have the keys and the bluetooth
    # flow will not
    flows = [
        flow
        for flow in hass.config_entries.flow.async_progress()
        if flow["handler"] == DOMAIN
    ]
    assert len(flows) == 1

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
        CONF_LOCAL_NAME: LOCK_DISCOVERY_INFO_UUID_ADDRESS.name,
        CONF_ADDRESS: LOCK_DISCOVERY_INFO_UUID_ADDRESS.address,
        CONF_KEY: "2fd51b8621c6a139eaffbedcb846b60f",
        CONF_SLOT: 66,
    }
    assert result2["result"].unique_id == OLD_FIRMWARE_LOCK_DISCOVERY_INFO.address
    assert len(mock_setup_entry.mock_calls) == 1
    flows = [
        flow
        for flow in hass.config_entries.flow.async_progress()
        if flow["handler"] == DOMAIN
    ]
    assert len(flows) == 0