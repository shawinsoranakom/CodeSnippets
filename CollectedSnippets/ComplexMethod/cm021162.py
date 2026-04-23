async def test_create_entry(
    hass: HomeAssistant,
    client,
    config,
    get_pickup_events_errors,
    get_pickup_events_mock,
    mock_aiorecollect,
) -> None:
    """Test creating an entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    # Test errors that can arise when checking the API key:
    with patch.object(client, "async_get_pickup_events", get_pickup_events_mock):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=config
        )
        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == get_pickup_events_errors

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=config
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == f"{TEST_PLACE_ID}, {TEST_SERVICE_ID}"
    assert result["data"] == {
        CONF_PLACE_ID: TEST_PLACE_ID,
        CONF_SERVICE_ID: TEST_SERVICE_ID,
    }