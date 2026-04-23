async def test_flow_chaining_with_next_flow(hass: HomeAssistant) -> None:
    """Test flow chaining when another integration registers a next flow."""
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
            return_value=None,
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
            data=IMPROV_BLE_DISCOVERY_INFO_TARGET1,
        )
        next_config_flow_id = target_result["flow_id"]

        # Simulate another integration discovering the device and registering a flow
        # This happens while provision is waiting on the future
        improv_ble.async_register_next_flow(
            hass, IMPROV_BLE_DISCOVERY_INFO.address, next_config_flow_id
        )

        await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "provision_successful"
    assert result["next_flow"] == (FlowType.CONFIG_FLOW, next_config_flow_id)