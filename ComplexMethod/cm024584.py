async def test_unprovided_days_are_none(
    hass: HomeAssistant,
    mock_bsblan: MagicMock,
    device_entry: dr.DeviceEntry,
) -> None:
    """Test that unprovided days are sent as None to BSB-LAN API."""
    # Only provide Monday and Tuesday, leave other days unprovided
    await hass.services.async_call(
        DOMAIN,
        "set_hot_water_schedule",
        {
            "device_id": device_entry.id,
            "monday_slots": [
                {"start_time": time(6, 0), "end_time": time(8, 0)},
            ],
            "tuesday_slots": [
                {"start_time": time(17, 0), "end_time": time(21, 0)},
            ],
        },
        blocking=True,
    )

    # Verify the API was called
    assert mock_bsblan.set_hot_water_schedule.called
    call_args = mock_bsblan.set_hot_water_schedule.call_args
    dhw_schedule = call_args.args[0]

    # Verify provided days have values
    assert dhw_schedule.monday == DaySchedule(
        slots=[TimeSlot(start=time(6, 0), end=time(8, 0))]
    )
    assert dhw_schedule.tuesday == DaySchedule(
        slots=[TimeSlot(start=time(17, 0), end=time(21, 0))]
    )

    # Verify unprovided days are None (not empty DaySchedule)
    assert dhw_schedule.wednesday is None
    assert dhw_schedule.thursday is None
    assert dhw_schedule.friday is None
    assert dhw_schedule.saturday is None
    assert dhw_schedule.sunday is None