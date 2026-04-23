async def test_full_user_flow_implementation(hass: HomeAssistant) -> None:
    """Test the full manual user flow from start to finish."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    assert result.get("step_id") == "user"
    assert result.get("type") is FlowResultType.FORM
    LOGGER.debug(result)
    assert result.get("data_schema") != ""
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_STATION_ID: TEST_STATION_ID},
    )
    assert result.get("type") is FlowResultType.CREATE_ENTRY
    assert "data" in result
    assert result["data"][CONF_STATION_ID] == TEST_STATION_ID
    assert "result" in result
    assert result["result"].unique_id == TEST_STATION_ID