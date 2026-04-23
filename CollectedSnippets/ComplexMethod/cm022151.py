async def test_user_step_discovered_devices(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, mock_service_info: None
) -> None:
    """Test we properly handle device picking."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "pick_device"

    with pytest.raises(vol.Invalid):
        await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_ADDRESS: "wrong_address"}
        )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_ADDRESS: FIXTURE_MAC}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "bluetooth_confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=FIXTURE_USER_INPUT
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].title == f"{FIXTURE_DEVICE_NAME} {FIXTURE_MAC}"
    assert result["result"].unique_id == FIXTURE_MAC
    assert result["result"].data == {
        CONF_ADDRESS: FIXTURE_MAC,
        CONF_PIN: FIXTURE_USER_INPUT[CONF_PIN],
    }
    mock_setup_entry.assert_called_once()