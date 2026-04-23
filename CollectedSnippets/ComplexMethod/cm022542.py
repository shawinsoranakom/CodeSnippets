async def test_if_fires_using_weekday_multiple(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    service_calls: list[ServiceCall],
) -> None:
    """Test for firing on multiple weekdays."""
    # Freeze time to Monday, January 2, 2023 at 5:00:00
    monday_trigger = dt_util.as_utc(datetime(2023, 1, 2, 5, 0, 0, 0))

    freezer.move_to(monday_trigger)

    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "time",
                    "at": "5:00:00",
                    "weekday": ["mon", "wed", "fri"],
                },
                "action": {
                    "service": "test.automation",
                    "data_template": {
                        "some": "{{ trigger.platform }} - {{ trigger.now.strftime('%A') }}",
                    },
                },
            }
        },
    )
    await hass.async_block_till_done()

    # Fire on Monday - should trigger
    async_fire_time_changed(hass, monday_trigger + timedelta(seconds=1))
    await hass.async_block_till_done()
    assert len(service_calls) == 1
    assert "Monday" in service_calls[0].data["some"]

    # Fire on Tuesday - should not trigger
    tuesday_trigger = dt_util.as_utc(datetime(2023, 1, 3, 5, 0, 0, 0))
    async_fire_time_changed(hass, tuesday_trigger)
    await hass.async_block_till_done()
    assert len(service_calls) == 1

    # Fire on Wednesday - should trigger
    wednesday_trigger = dt_util.as_utc(datetime(2023, 1, 4, 5, 0, 0, 0))
    async_fire_time_changed(hass, wednesday_trigger)
    await hass.async_block_till_done()
    assert len(service_calls) == 2
    assert "Wednesday" in service_calls[1].data["some"]

    # Fire on Friday - should trigger
    friday_trigger = dt_util.as_utc(datetime(2023, 1, 6, 5, 0, 0, 0))
    async_fire_time_changed(hass, friday_trigger)
    await hass.async_block_till_done()
    assert len(service_calls) == 3
    assert "Friday" in service_calls[2].data["some"]