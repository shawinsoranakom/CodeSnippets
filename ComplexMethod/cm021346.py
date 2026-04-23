async def _test_common_success_with_identify(
    hass: HomeAssistant, result: FlowResult, address: str
) -> None:
    """Test bluetooth and user flow success paths."""
    with (
        patch(
            f"{IMPROV_BLE}.config_flow.ImprovBLEClient.can_identify",
            return_value=True,
            new_callable=PropertyMock,
        ),
        patch(f"{IMPROV_BLE}.config_flow.ImprovBLEClient.ensure_connected"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ADDRESS: address},
        )
    assert result["type"] is FlowResultType.MENU
    assert result["menu_options"] == ["identify", "provision"]
    assert result["step_id"] == "main_menu"

    with patch(f"{IMPROV_BLE}.config_flow.ImprovBLEClient.identify"):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"next_step_id": "identify"},
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "identify"
    assert result["errors"] is None

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.MENU
    assert result["menu_options"] == ["identify", "provision"]
    assert result["step_id"] == "main_menu"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "provision"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "provision"
    assert result["errors"] is None

    await _test_common_success(hass, result)