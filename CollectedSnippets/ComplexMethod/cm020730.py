async def test_create_entry(hass: HomeAssistant, client, config, mock_pyopenuv) -> None:
    """Test creating an entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    # Test an error occurring:
    with patch.object(client, "uv_index", AsyncMock(side_effect=InvalidApiKeyError)):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=config
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"
        assert result["errors"] == {CONF_API_KEY: "invalid_api_key"}

    # Test that we can recover from the error:
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=config
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == f"{TEST_LATITUDE}, {TEST_LONGITUDE}"
    assert result["data"] == {
        CONF_API_KEY: TEST_API_KEY,
        CONF_ELEVATION: TEST_ELEVATION,
        CONF_LATITUDE: TEST_LATITUDE,
        CONF_LONGITUDE: TEST_LONGITUDE,
    }