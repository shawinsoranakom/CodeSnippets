async def test_create_entry_by_coordinates(
    hass: HomeAssistant,
    api,
    check_api_key_errors,
    check_api_key_mock,
    get_nearby_sensors_errors,
    get_nearby_sensors_mock,
    mock_aiopurpleair,
) -> None:
    """Test creating an entry by entering a latitude/longitude (including errors)."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    # Test errors that can arise when checking the API key:
    with patch.object(api, "async_check_api_key", check_api_key_mock):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={"api_key": TEST_API_KEY}
        )
        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == check_api_key_errors

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"api_key": TEST_API_KEY}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "by_coordinates"

    # Test errors that can arise when searching for nearby sensors:
    with patch.object(api.sensors, "async_get_nearby_sensors", get_nearby_sensors_mock):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                "latitude": TEST_LATITUDE,
                "longitude": TEST_LONGITUDE,
                "distance": 5,
            },
        )
        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == get_nearby_sensors_errors

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            "latitude": TEST_LATITUDE,
            "longitude": TEST_LONGITUDE,
            "distance": 5,
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "choose_sensor"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            "sensor_index": str(TEST_SENSOR_INDEX1),
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "abcde"
    assert result["data"] == {
        "api_key": TEST_API_KEY,
    }
    assert result["options"] == {
        "sensor_indices": [TEST_SENSOR_INDEX1],
    }