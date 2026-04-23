async def _test_common_success_w_authorize(
    hass: HomeAssistant, result: FlowResult
) -> None:
    """Test bluetooth and user flow success paths."""

    async def subscribe_state_updates(
        state_callback: Callable[[State], None],
    ) -> Callable[[], None]:
        state_callback(State.AUTHORIZED)
        return lambda: None

    with (
        patch(
            f"{IMPROV_BLE}.config_flow.ImprovBLEClient.need_authorization",
            return_value=True,
        ),
        patch(
            f"{IMPROV_BLE}.config_flow.ImprovBLEClient.subscribe_state_updates",
            side_effect=subscribe_state_updates,
        ) as mock_subscribe_state_updates,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"ssid": "MyWIFI", "password": "secret"}
        )
        assert result["type"] is FlowResultType.SHOW_PROGRESS
        assert result["progress_action"] == "authorize"
        assert result["step_id"] == "authorize"
        mock_subscribe_state_updates.assert_awaited_once()
        await hass.async_block_till_done()

    with (
        patch(
            f"{IMPROV_BLE}.config_flow.ImprovBLEClient.need_authorization",
            return_value=False,
        ),
        patch(
            f"{IMPROV_BLE}.config_flow.ImprovBLEClient.provision",
            return_value="http://blabla.local",
        ) as mock_provision,
        patch(f"{IMPROV_BLE}.config_flow.PROVISIONING_TIMEOUT", 0.0000001),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"])
        assert result["type"] is FlowResultType.SHOW_PROGRESS
        assert result["progress_action"] == "provisioning"
        assert result["step_id"] == "do_provision"
        await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    assert result["description_placeholders"] == {"url": "http://blabla.local"}
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "provision_successful_url"

    mock_provision.assert_awaited_once_with("MyWIFI", "secret", None)