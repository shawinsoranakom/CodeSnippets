async def test_async_step_bluetooth_valid_device(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test discovery via bluetooth with a valid device."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_BLUETOOTH},
        data=VICTRON_VEBUS_SERVICE_INFO,
    )
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "access_token"

    # test valid access token
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_ACCESS_TOKEN: VICTRON_VEBUS_TOKEN},
    )
    assert result.get("type") is FlowResultType.CREATE_ENTRY
    assert result.get("title") == VICTRON_VEBUS_SERVICE_INFO.name
    flow_result = result.get("result")
    assert flow_result is not None
    assert flow_result.unique_id == VICTRON_VEBUS_SERVICE_INFO.address
    assert flow_result.data == {
        CONF_ACCESS_TOKEN: VICTRON_VEBUS_TOKEN,
    }
    assert set(flow_result.data.keys()) == {CONF_ACCESS_TOKEN}