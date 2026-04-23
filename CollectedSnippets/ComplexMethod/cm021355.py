async def test_flow_chaining_with_redirect_url(hass: HomeAssistant) -> None:
    """Test flow chaining takes precedence over redirect URL."""
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

    with (
        patch(
            f"{IMPROV_BLE}.config_flow.ImprovBLEClient.need_authorization",
            return_value=False,
        ),
        patch(
            f"{IMPROV_BLE}.config_flow.ImprovBLEClient.provision",
            return_value="http://blabla.local",
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"ssid": "TestNetwork", "password": "secret"}
        )
        assert result["type"] is FlowResultType.SHOW_PROGRESS
        assert result["progress_action"] == "provisioning"
        assert result["step_id"] == "do_provision"

        # Yield to allow the background task to create the future
        await asyncio.sleep(0)  # task is created with eager_start=False

        # Create a dummy target flow using a different device address
        target_result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_BLUETOOTH},
            data=IMPROV_BLE_DISCOVERY_INFO_TARGET2,
        )
        esphome_flow_id = target_result["flow_id"]

        # Simulate ESPHome discovering the device and notifying Improv BLE
        # This happens while provision is still running
        improv_ble.async_register_next_flow(
            hass, IMPROV_BLE_DISCOVERY_INFO.address, esphome_flow_id
        )

        await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    assert result["type"] is FlowResultType.ABORT
    # Should use next_flow instead of redirect URL
    assert result["reason"] == "provision_successful"
    assert result["next_flow"] == (FlowType.CONFIG_FLOW, esphome_flow_id)