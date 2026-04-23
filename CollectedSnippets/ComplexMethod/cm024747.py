async def test_bluetooth_not_paired(
    hass: HomeAssistant,
    mock_automower_client: Mock,
) -> None:
    """Test we can select a device."""

    inject_bluetooth_service_info(hass, AUTOMOWER_SERVICE_INFO_SERIAL)
    await hass.async_block_till_done(wait_background_tasks=True)

    result = hass.config_entries.flow.async_progress_by_handler(DOMAIN)[0]
    assert result["step_id"] == "bluetooth_confirm"

    mock_automower_client.connect.return_value = ResponseResult.NOT_ALLOWED

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PIN: "5678"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "bluetooth_confirm"

    mock_automower_client.connect.return_value = ResponseResult.OK

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PIN: "1234"},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Husqvarna Automower"
    assert result["result"].unique_id == "00000000-0000-0000-0000-000000000003"

    assert result["data"] == {
        CONF_ADDRESS: "00000000-0000-0000-0000-000000000003",
        CONF_CLIENT_ID: 1197489078,
        CONF_PIN: "1234",
    }