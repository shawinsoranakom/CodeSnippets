async def test_options_add_sensor(
    hass: HomeAssistant,
    mock_aiopurpleair,
    config_entry,
    get_nearby_sensors_errors,
    get_nearby_sensors_mock,
    setup_config_entry,
) -> None:
    """Test adding a sensor via the options flow (including errors)."""
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={"next_step_id": "add_sensor"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "add_sensor"

    # Test errors that can arise when searching for nearby sensors:
    with patch.object(
        mock_aiopurpleair.sensors, "async_get_nearby_sensors", get_nearby_sensors_mock
    ):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                "latitude": TEST_LATITUDE,
                "longitude": TEST_LONGITUDE,
                "distance": 5,
            },
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "add_sensor"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "latitude": TEST_LATITUDE,
            "longitude": TEST_LONGITUDE,
            "distance": 5,
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "choose_sensor"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "sensor_index": str(TEST_SENSOR_INDEX2),
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "sensor_indices": [TEST_SENSOR_INDEX1, TEST_SENSOR_INDEX2],
    }

    assert config_entry.options["sensor_indices"] == [
        TEST_SENSOR_INDEX1,
        TEST_SENSOR_INDEX2,
    ]
    # Unload to make sure the update does not run after the
    # mock is removed.
    await hass.config_entries.async_unload(config_entry.entry_id)