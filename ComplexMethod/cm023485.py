async def test_async_step_user_with_devices_found(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_discovered_service_info: AsyncMock,
) -> None:
    """Test setup from service info cache with devices found."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_ADDRESS: VICTRON_VEBUS_SERVICE_INFO.address},
    )
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "access_token"

    # test invalid access token shows error and allows retry
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_ACCESS_TOKEN: VICTRON_TEST_WRONG_TOKEN}
    )
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "access_token"
    assert result.get("errors") == {"base": "invalid_access_token"}

    # test retry with valid access token succeeds
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_ACCESS_TOKEN: VICTRON_VEBUS_TOKEN},
    )
    assert result.get("type") is FlowResultType.CREATE_ENTRY
    assert result.get("title") == VICTRON_VEBUS_SERVICE_INFO.name