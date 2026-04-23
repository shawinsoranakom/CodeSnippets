async def test_service_set_charge_schedule_multi(
    hass: HomeAssistant, config_entry: ConfigEntry, snapshot: SnapshotAssertion
) -> None:
    """Test that service invokes renault_api with correct data."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    schedules = [
        {
            "id": 2,
            "activated": True,
            "monday": {"startTime": "T12:00Z", "duration": 30},
            "tuesday": {"startTime": "T12:00Z", "duration": 30},
            "wednesday": None,
            "friday": {"startTime": "T12:00Z", "duration": 30},
            "saturday": {"startTime": "T12:00Z", "duration": 30},
            "sunday": {"startTime": "T12:00Z", "duration": 30},
        },
        {"id": 3},
    ]
    data = {
        ATTR_VEHICLE: get_device_id(hass),
        ATTR_SCHEDULES: schedules,
    }

    with (
        patch("renault_api.renault_vehicle.RenaultVehicle.get_full_endpoint"),
        patch(
            "renault_api.renault_vehicle.RenaultVehicle.http_get",
            return_value=schemas.KamereonResponseSchema.loads(
                await async_load_fixture(hass, "charging_settings.json", DOMAIN)
            ),
        ),
        patch(
            "renault_api.renault_vehicle.RenaultVehicle.set_charge_schedules",
            return_value=(
                schemas.KamereonVehicleHvacStartActionDataSchema.loads(
                    await async_load_fixture(
                        hass, "action.set_charge_schedules.json", DOMAIN
                    )
                )
            ),
        ) as mock_action,
    ):
        await hass.services.async_call(
            DOMAIN, "charge_set_schedules", service_data=data, blocking=True
        )
    assert len(mock_action.mock_calls) == 1
    mock_call_data: list[ChargeSchedule] = mock_action.mock_calls[0][1][0]
    assert mock_call_data == snapshot

    # Monday updated with new values
    assert mock_call_data[1].monday.startTime == "T12:00Z"
    assert mock_call_data[1].monday.duration == 30
    # Wednesday has original values cleared
    assert mock_call_data[1].wednesday is None
    # Thursday keeps original values
    assert mock_call_data[1].thursday.startTime == "T23:30Z"
    assert mock_call_data[1].thursday.duration == 15