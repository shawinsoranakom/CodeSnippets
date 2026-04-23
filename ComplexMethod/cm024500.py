async def test_create_entry(
    hass: HomeAssistant, api, config, devices_response, errors, mock_aioambient
) -> None:
    """Test creating an entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    # Test errors that can arise:
    with patch.object(api, "get_devices", devices_response):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=config
        )
        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == errors

    # Test that we can recover and finish the flow after errors occur:
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=config
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "67890fghij67"
    assert result["data"] == {
        CONF_API_KEY: "12345abcde12345abcde",
        CONF_APP_KEY: "67890fghij67890fghij",
    }