async def test_vehicle_without_location_scope(
    hass: HomeAssistant,
    expires_at: int,
    mock_vehicle_data: AsyncMock,
) -> None:
    """Test vehicle setup without VEHICLE_LOCATION scope excludes location endpoint."""

    # Create config entry without VEHICLE_LOCATION scope
    config_entry = create_config_entry(
        expires_at,
        [
            Scope.OPENID,
            Scope.OFFLINE_ACCESS,
            Scope.VEHICLE_DEVICE_DATA,
            # Deliberately exclude Scope.VEHICLE_LOCATION
        ],
    )

    await setup_platform(hass, config_entry)
    assert config_entry.state is ConfigEntryState.LOADED

    # Verify that vehicle_data was called without LOCATION_DATA endpoint
    mock_vehicle_data.assert_called()
    call_args = mock_vehicle_data.call_args
    endpoints = call_args.kwargs.get("endpoints", [])

    # Should not include LOCATION_DATA endpoint
    assert VehicleDataEndpoint.LOCATION_DATA not in endpoints

    # Should include other endpoints
    assert VehicleDataEndpoint.CHARGE_STATE in endpoints
    assert VehicleDataEndpoint.CLIMATE_STATE in endpoints
    assert VehicleDataEndpoint.DRIVE_STATE in endpoints
    assert VehicleDataEndpoint.VEHICLE_STATE in endpoints
    assert VehicleDataEndpoint.VEHICLE_CONFIG in endpoints