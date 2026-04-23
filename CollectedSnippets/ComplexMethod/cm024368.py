async def test_list_statistic_ids(
    hass: HomeAssistant,
    state_class: str | SensorStateClass,
    device_class: str | SensorDeviceClass,
    state_unit: str,
    display_unit: str,
    statistics_unit: str,
    unit_class: str | None,
    statistic_type: str | StatisticMeanType,
) -> None:
    """Test listing future statistic ids."""
    await async_setup_component(hass, "sensor", {})
    # Wait for the sensor recorder platform to be added
    await async_recorder_block_till_done(hass)
    attributes = {
        "device_class": device_class,
        "last_reset": 0,
        "state_class": state_class,
        "unit_of_measurement": state_unit,
    }
    hass.states.async_set("sensor.test1", 0, attributes=attributes)
    statistic_ids = await async_list_statistic_ids(hass)
    mean_type = (
        statistic_type
        if isinstance(statistic_type, StatisticMeanType)
        else StatisticMeanType.NONE
    )
    statistic_type = (
        statistic_type if not isinstance(statistic_type, StatisticMeanType) else "mean"
    )
    assert statistic_ids == [
        {
            "statistic_id": "sensor.test1",
            "display_unit_of_measurement": display_unit,
            "has_mean": mean_type is StatisticMeanType.ARITHMETIC,
            "mean_type": mean_type,
            "has_sum": statistic_type == "sum",
            "name": None,
            "source": "recorder",
            "statistics_unit_of_measurement": statistics_unit,
            "unit_class": unit_class,
        },
    ]

    for stat_type in ("mean", "sum", "dogs"):
        statistic_ids = await async_list_statistic_ids(hass, statistic_type=stat_type)
        if statistic_type == stat_type:
            assert statistic_ids == [
                {
                    "statistic_id": "sensor.test1",
                    "display_unit_of_measurement": display_unit,
                    "has_mean": mean_type is StatisticMeanType.ARITHMETIC,
                    "mean_type": mean_type,
                    "has_sum": statistic_type == "sum",
                    "name": None,
                    "source": "recorder",
                    "statistics_unit_of_measurement": statistics_unit,
                    "unit_class": unit_class,
                },
            ]
        else:
            assert statistic_ids == []