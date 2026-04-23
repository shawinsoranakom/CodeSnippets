async def test_reconfigure_fails(
    hass: HomeAssistant,
    mock_vodafone_station_router: AsyncMock,
    mock_setup_entry: AsyncMock,
    mock_config_entry: MockConfigEntry,
    side_effect: Exception,
    error: str,
) -> None:
    """Test that the host can be reconfigured."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reconfigure_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    mock_vodafone_station_router.login.side_effect = side_effect

    reconfigure_result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "192.168.100.60",
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_USERNAME: TEST_USERNAME,
        },
    )

    assert reconfigure_result["type"] is FlowResultType.FORM
    assert reconfigure_result["step_id"] == "reconfigure"
    assert reconfigure_result["errors"] == {"base": error}

    mock_vodafone_station_router.login.side_effect = None

    reconfigure_result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "192.168.100.61",
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_USERNAME: TEST_USERNAME,
        },
    )

    assert reconfigure_result["type"] is FlowResultType.ABORT
    assert reconfigure_result["reason"] == "reconfigure_successful"
    assert mock_config_entry.data == {
        CONF_HOST: "192.168.100.61",
        CONF_PASSWORD: TEST_PASSWORD,
        CONF_USERNAME: TEST_USERNAME,
        CONF_DEVICE_DETAILS: {
            DEVICE_TYPE: TEST_TYPE,
            DEVICE_URL: TEST_URL,
        },
    }