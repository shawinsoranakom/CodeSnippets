async def test_integration_discovery_takes_precedence_over_bluetooth_non_unique_local_name(
    hass: HomeAssistant,
) -> None:
    """Test integration discovery dismisses bluetooth discovery with a non unique local name."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=OLD_FIRMWARE_LOCK_DISCOVERY_INFO,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "key_slot"
    assert result["errors"] == {}
    flows = list(hass.config_entries.flow._handler_progress_index[DOMAIN])
    assert len(flows) == 1
    assert flows[0].unique_id == OLD_FIRMWARE_LOCK_DISCOVERY_INFO.address
    assert flows[0].local_name == OLD_FIRMWARE_LOCK_DISCOVERY_INFO.name

    with patch(
        "homeassistant.components.yalexs_ble.util.async_discovered_service_info",
        return_value=[OLD_FIRMWARE_LOCK_DISCOVERY_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_INTEGRATION_DISCOVERY},
            data={
                "name": "Front Door",
                "address": OLD_FIRMWARE_LOCK_DISCOVERY_INFO.address,
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