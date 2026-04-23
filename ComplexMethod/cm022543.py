async def test_if_fires_using_weekday_with_entity(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    service_calls: list[ServiceCall],
) -> None:
    """Test for firing on weekday with input_datetime entity."""
    await async_setup_component(
        hass,
        "input_datetime",
        {"input_datetime": {"trigger": {"has_date": False, "has_time": True}}},
    )

    # Freeze time to Monday, January 2, 2023 at 5:00:00
    monday_trigger = dt_util.as_utc(datetime(2023, 1, 2, 5, 0, 0, 0))

    await hass.services.async_call(
        "input_datetime",
        "set_datetime",
        {
            ATTR_ENTITY_ID: "input_datetime.trigger",
            "time": "05:00:00",
        },
        blocking=True,
    )

    freezer.move_to(monday_trigger)

    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "time",
                    "at": "input_datetime.trigger",
                    "weekday": "mon",
                },
                "action": {
                    "service": "test.automation",
                    "data_template": {
                        "some": "{{ trigger.platform }} - {{ trigger.now.strftime('%A') }}",
                        "entity": "{{ trigger.entity_id }}",
                    },
                },
            }
        },
    )
    await hass.async_block_till_done()

    # Fire on Monday - should trigger
    async_fire_time_changed(hass, monday_trigger + timedelta(seconds=1))
    await hass.async_block_till_done()
    automation_calls = [call for call in service_calls if call.domain == "test"]
    assert len(automation_calls) == 1
    assert "Monday" in automation_calls[0].data["some"]
    assert automation_calls[0].data["entity"] == "input_datetime.trigger"

    # Fire on Tuesday - should not trigger
    tuesday_trigger = dt_util.as_utc(datetime(2023, 1, 3, 5, 0, 0, 0))
    async_fire_time_changed(hass, tuesday_trigger)
    await hass.async_block_till_done()
    automation_calls = [call for call in service_calls if call.domain == "test"]
    assert len(automation_calls) == 1