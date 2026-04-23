async def test_vehicle_with_location_scope(
    hass: HomeAssistant,
    normal_config_entry: MockConfigEntry,
    mock_vehicle_data: AsyncMock,
) -> None:
    """Test vehicle setup with VEHICLE_LOCATION scope includes location endpoint."""
    await setup_platform(hass, normal_config_entry)
    assert normal_config_entry.state is ConfigEntryState.LOADED

    # Verify that vehicle_data was called with LOCATION_DATA endpoint
    mock_vehicle_data.assert_called()
    call_args = mock_vehicle_data.call_args
    endpoints = call_args.kwargs.get("endpoints", [])

    # Should include LOCATION_DATA endpoint when scope is present
    assert VehicleDataEndpoint.LOCATION_DATA in endpoints

    # Should include all other endpoints
    assert VehicleDataEndpoint.CHARGE_STATE in endpoints
    assert VehicleDataEndpoint.CLIMATE_STATE in endpoints
    assert VehicleDataEndpoint.DRIVE_STATE in endpoints
    assert VehicleDataEndpoint.VEHICLE_STATE in endpoints
    assert VehicleDataEndpoint.VEHICLE_CONFIG in endpoints