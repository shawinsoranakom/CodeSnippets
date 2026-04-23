async def test_if_fires_using_at_sensor(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    service_calls: list[ServiceCall],
    at_sensor: str,
) -> None:
    """Test for firing at sensor time."""
    now = dt_util.now()

    trigger_dt = now.replace(hour=5, minute=0, second=0, microsecond=0) + timedelta(2)

    hass.states.async_set(
        "sensor.next_alarm",
        trigger_dt.isoformat(),
        {ATTR_DEVICE_CLASS: SensorDeviceClass.TIMESTAMP},
    )

    time_that_will_not_match_right_away = trigger_dt - timedelta(minutes=1)

    some_data = "{{ trigger.platform }}-{{ trigger.now.day }}-{{ trigger.now.hour }}-{{trigger.entity_id}}"

    freezer.move_to(dt_util.as_utc(time_that_will_not_match_right_away))
    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {"platform": "time", "at": at_sensor},
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

    assert len(service_calls) == 1
    assert (
        service_calls[0].data["some"]
        == f"time-{trigger_dt.day}-{trigger_dt.hour}-sensor.next_alarm"
    )

    trigger_dt += timedelta(days=1, hours=1)

    hass.states.async_set(
        "sensor.next_alarm",
        trigger_dt.isoformat(),
        {ATTR_DEVICE_CLASS: SensorDeviceClass.TIMESTAMP},
    )
    await hass.async_block_till_done()

    async_fire_time_changed(hass, trigger_dt + timedelta(seconds=1))
    await hass.async_block_till_done()

    assert len(service_calls) == 2
    assert (
        service_calls[1].data["some"]
        == f"time-{trigger_dt.day}-{trigger_dt.hour}-sensor.next_alarm"
    )

    for broken in ("unknown", "unavailable", "invalid-ts"):
        hass.states.async_set(
            "sensor.next_alarm",
            trigger_dt.isoformat(),
            {ATTR_DEVICE_CLASS: SensorDeviceClass.TIMESTAMP},
        )
        await hass.async_block_till_done()
        hass.states.async_set(
            "sensor.next_alarm",
            broken,
            {ATTR_DEVICE_CLASS: SensorDeviceClass.TIMESTAMP},
        )
        await hass.async_block_till_done()

        async_fire_time_changed(hass, trigger_dt + timedelta(seconds=1))
        await hass.async_block_till_done()

        # We should not have listened to anything
        assert len(service_calls) == 2

    # Now without device class
    hass.states.async_set(
        "sensor.next_alarm",
        trigger_dt.isoformat(),
        {ATTR_DEVICE_CLASS: SensorDeviceClass.TIMESTAMP},
    )
    await hass.async_block_till_done()
    hass.states.async_set(
        "sensor.next_alarm",
        trigger_dt.isoformat(),
    )
    await hass.async_block_till_done()

    async_fire_time_changed(hass, trigger_dt + timedelta(seconds=1))
    await hass.async_block_till_done()

    # We should not have listened to anything
    assert len(service_calls) == 2