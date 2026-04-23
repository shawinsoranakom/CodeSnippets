def _get_fixtures(vehicle_type: str) -> MappingProxyType:
    """Create a vehicle proxy for testing."""
    mock_vehicle = MOCK_VEHICLES.get(vehicle_type, {"endpoints": {}})
    return {
        "battery_status": schemas.KamereonVehicleDataResponseSchema.loads(
            load_fixture(f"renault/{mock_vehicle['endpoints']['battery_status']}")
            if "battery_status" in mock_vehicle["endpoints"]
            else load_fixture("renault/no_data.json")
        ).get_attributes(schemas.KamereonVehicleBatteryStatusDataSchema),
        "battery_soc": schemas.KamereonVehicleDataResponseSchema.loads(
            load_fixture(f"renault/{mock_vehicle['endpoints']['battery_soc']}")
            if "battery_soc" in mock_vehicle["endpoints"]
            else load_fixture("renault/no_data.json")
        ).get_attributes(schemas.KamereonVehicleBatterySocDataSchema),
        "charge_mode": schemas.KamereonVehicleDataResponseSchema.loads(
            load_fixture(f"renault/{mock_vehicle['endpoints']['charge_mode']}")
            if "charge_mode" in mock_vehicle["endpoints"]
            else load_fixture("renault/no_data.json")
        ).get_attributes(schemas.KamereonVehicleChargeModeDataSchema),
        "charging_settings": schemas.KamereonVehicleDataResponseSchema.loads(
            load_fixture(f"renault/{mock_vehicle['endpoints']['charging_settings']}")
            if "charging_settings" in mock_vehicle["endpoints"]
            else load_fixture("renault/no_data.json")
        ).get_attributes(schemas.KamereonVehicleChargingSettingsDataSchema),
        "cockpit": schemas.KamereonVehicleDataResponseSchema.loads(
            load_fixture(f"renault/{mock_vehicle['endpoints']['cockpit']}")
            if "cockpit" in mock_vehicle["endpoints"]
            else load_fixture("renault/no_data.json")
        ).get_attributes(schemas.KamereonVehicleCockpitDataSchema),
        "hvac_status": schemas.KamereonVehicleDataResponseSchema.loads(
            load_fixture(f"renault/{mock_vehicle['endpoints']['hvac_status']}")
            if "hvac_status" in mock_vehicle["endpoints"]
            else load_fixture("renault/no_data.json")
        ).get_attributes(schemas.KamereonVehicleHvacStatusDataSchema),
        "location": schemas.KamereonVehicleDataResponseSchema.loads(
            load_fixture(f"renault/{mock_vehicle['endpoints']['location']}")
            if "location" in mock_vehicle["endpoints"]
            else load_fixture("renault/no_data.json")
        ).get_attributes(schemas.KamereonVehicleLocationDataSchema),
        "lock_status": schemas.KamereonVehicleDataResponseSchema.loads(
            load_fixture(f"renault/{mock_vehicle['endpoints']['lock_status']}")
            if "lock_status" in mock_vehicle["endpoints"]
            else load_fixture("renault/no_data.json")
        ).get_attributes(schemas.KamereonVehicleLockStatusDataSchema),
        "res_state": schemas.KamereonVehicleDataResponseSchema.loads(
            load_fixture(f"renault/{mock_vehicle['endpoints']['res_state']}")
            if "res_state" in mock_vehicle["endpoints"]
            else load_fixture("renault/no_data.json")
        ).get_attributes(schemas.KamereonVehicleResStateDataSchema),
        "pressure": schemas.KamereonVehicleDataResponseSchema.loads(
            load_fixture(f"renault/{mock_vehicle['endpoints']['pressure']}")
            if "pressure" in mock_vehicle["endpoints"]
            else load_fixture("renault/no_data.json")
        ).get_attributes(schemas.KamereonVehicleTyrePressureDataSchema),
    }