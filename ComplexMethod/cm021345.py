async def test_bluetooth_rediscovery_after_successful_provision(
    hass: HomeAssistant,
) -> None:
    """Test that device can be rediscovered after successful provisioning."""
    # Start provisioning flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=IMPROV_BLE_DISCOVERY_INFO,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "bluetooth_confirm"

    # Confirm bluetooth setup
    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "bluetooth_confirm"

    # Start provisioning
    with (
        patch(
            f"{IMPROV_BLE}.config_flow.ImprovBLEClient.can_identify",
            return_value=False,
            new_callable=PropertyMock,
        ),
        patch(f"{IMPROV_BLE}.config_flow.ImprovBLEClient.ensure_connected"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ADDRESS: IMPROV_BLE_DISCOVERY_INFO.address},
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "provision"

    # Complete provisioning successfully
    with (
        patch(
            f"{IMPROV_BLE}.config_flow.ImprovBLEClient.need_authorization",
            return_value=False,
        ),
        patch(
            f"{IMPROV_BLE}.config_flow.ImprovBLEClient.provision",
            return_value=None,
        ),
        patch(f"{IMPROV_BLE}.config_flow.PROVISIONING_TIMEOUT", 0.0000001),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"ssid": "TestNetwork", "password": "secret"}
        )
        assert result["type"] is FlowResultType.SHOW_PROGRESS
        assert result["progress_action"] == "provisioning"
        assert result["step_id"] == "do_provision"
        await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "provision_successful"

    # Now inject the same device again (simulating factory reset)
    # The match history was cleared after successful provision, so it should be rediscovered
    inject_bluetooth_service_info_bleak(hass, IMPROV_BLE_DISCOVERY_INFO)
    await hass.async_block_till_done()

    # Verify new discovery flow was created
    flows = hass.config_entries.flow.async_progress_by_handler(DOMAIN)
    assert len(flows) == 1
    assert flows[0]["step_id"] == "bluetooth_confirm"