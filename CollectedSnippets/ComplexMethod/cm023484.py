async def test_async_step_bluetooth_invalid_key_retry(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test wrong key via bluetooth discovery shows error and allows retry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_BLUETOOTH},
        data=VICTRON_VEBUS_SERVICE_INFO,
    )
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "access_token"

    # enter wrong key
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_ACCESS_TOKEN: VICTRON_TEST_WRONG_TOKEN},
    )
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "access_token"
    assert result.get("errors") == {"base": "invalid_access_token"}

    # retry with correct key
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_ACCESS_TOKEN: VICTRON_VEBUS_TOKEN},
    )
    assert result.get("type") is FlowResultType.CREATE_ENTRY
    assert result.get("title") == VICTRON_VEBUS_SERVICE_INFO.name