async def test_if_fires_using_at_input_datetime(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    service_calls: list[ServiceCall],
    has_date,
    has_time,
) -> None:
    """Test for firing at input_datetime."""
    await async_setup_component(
        hass,
        "input_datetime",
        {"input_datetime": {"trigger": {"has_date": has_date, "has_time": has_time}}},
    )
    now = dt_util.now()

    trigger_dt = now.replace(
        hour=5 if has_time else 0, minute=0, second=0, microsecond=0
    ) + timedelta(2)

    await hass.services.async_call(
        "input_datetime",
        "set_datetime",
        {
            ATTR_ENTITY_ID: "input_datetime.trigger",
            "datetime": str(trigger_dt.replace(tzinfo=None)),
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    time_that_will_not_match_right_away = trigger_dt - timedelta(minutes=1)

    some_data = "{{ trigger.platform }}-{{ trigger.now.day }}-{{ trigger.now.hour }}-{{trigger.entity_id}}"

    freezer.move_to(dt_util.as_utc(time_that_will_not_match_right_away))
    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {"platform": "time", "at": "input_datetime.trigger"},
                "action": {
                    "service": "test.automation",
                    "data_template": {"some": some_data},
                },
            }
        },
    )
    await hass.async_block_till_done()

    async_fire_time_changed(hass, trigger_dt + timedelta(seconds=1))
    await hass.async_block_till_done()

    assert len(service_calls) == 2
    assert (
        service_calls[1].data["some"]
        == f"time-{trigger_dt.day}-{trigger_dt.hour}-input_datetime.trigger"
    )

    if has_date:
        trigger_dt += timedelta(days=1)
    if has_time:
        trigger_dt += timedelta(hours=1)

    await hass.services.async_call(
        "input_datetime",
        "set_datetime",
        {
            ATTR_ENTITY_ID: "input_datetime.trigger",
            "datetime": str(trigger_dt.replace(tzinfo=None)),
        },
        blocking=True,
    )
    assert len(service_calls) == 3
    await hass.async_block_till_done()

    async_fire_time_changed(hass, trigger_dt + timedelta(seconds=1))
    await hass.async_block_till_done()

    assert len(service_calls) == 4
    assert (
        service_calls[3].data["some"]
        == f"time-{trigger_dt.day}-{trigger_dt.hour}-input_datetime.trigger"
    )