async def test_state_characteristics(hass: HomeAssistant) -> None:
    """Test configured state characteristic for value and unit."""
    now = dt_util.utcnow()
    current_time = datetime(now.year + 1, 8, 2, 12, 23, 42, tzinfo=dt_util.UTC)
    start_datetime = datetime(now.year + 1, 8, 2, 12, 23, 42, tzinfo=dt_util.UTC)
    characteristics: Sequence[dict[str, Any]] = (
        {
            "source_sensor_domain": "sensor",
            "name": "average_linear",
            "value_0": STATE_UNKNOWN,
            "value_1": 6.0,
            "value_9": 10.68,
            "unit": "°C",
        },
        {
            "source_sensor_domain": "sensor",
            "name": "average_step",
            "value_0": STATE_UNKNOWN,
            "value_1": 6.0,
            "value_9": 11.36,
            "unit": "°C",
        },
        {
            "source_sensor_domain": "sensor",
            "name": "average_timeless",
            "value_0": STATE_UNKNOWN,
            "value_1": float(VALUES_NUMERIC[-1]),
            "value_9": float(round(sum(VALUES_NUMERIC) / len(VALUES_NUMERIC), 2)),
            "unit": "°C",
        },
        {
            "source_sensor_domain": "sensor",
            "name": "change",
            "value_0": STATE_UNKNOWN,
            "value_1": float(0),
            "value_9": float(round(VALUES_NUMERIC[-1] - VALUES_NUMERIC[0], 2)),
            "unit": "°C",
        },
        {
            "source_sensor_domain": "sensor",
            "name": "change_sample",
            "value_0": STATE_UNKNOWN,
            "value_1": STATE_UNKNOWN,
            "value_9": float(
                round(
                    (VALUES_NUMERIC[-1] - VALUES_NUMERIC[0])
                    / (len(VALUES_NUMERIC) - 1),
                    2,
                )
            ),
            "unit": "°C/sample",
        },
        {
            "source_sensor_domain": "sensor",
            "name": "change_second",
            "value_0": STATE_UNKNOWN,
            "value_1": STATE_UNKNOWN,
            "value_9": float(
                round(
                    (VALUES_NUMERIC[-1] - VALUES_NUMERIC[0])
                    / (60 * (len(VALUES_NUMERIC) - 1)),
                    2,
                )
            ),
            "unit": "°C/s",
        },
        {
            "source_sensor_domain": "sensor",
            "name": "count",
            "value_0": 0,
            "value_1": 1,
            "value_9": 9,
            "unit": None,
        },
        {
            "source_sensor_domain": "sensor",
            "name": "datetime_newest",
            "value_0": STATE_UNKNOWN,
            "value_1": (start_datetime + timedelta(minutes=9)).isoformat(),
            "value_9": (start_datetime + timedelta(minutes=9)).isoformat(),
            "unit": None,
        },
        {
            "source_sensor_domain": "sensor",
            "name": "datetime_oldest",
            "value_0": STATE_UNKNOWN,
            "value_1": (start_datetime + timedelta(minutes=9)).isoformat(),
            "value_9": (start_datetime + timedelta(minutes=1)).isoformat(),
            "unit": None,
        },
        {
            "source_sensor_domain": "sensor",
            "name": "datetime_value_max",
            "value_0": STATE_UNKNOWN,
            "value_1": (start_datetime + timedelta(minutes=9)).isoformat(),
            "value_9": (start_datetime + timedelta(minutes=2)).isoformat(),
            "unit": None,
        },
        {
            "source_sensor_domain": "sensor",
            "name": "datetime_value_min",
            "value_0": STATE_UNKNOWN,
            "value_1": (start_datetime + timedelta(minutes=9)).isoformat(),
            "value_9": (start_datetime + timedelta(minutes=5)).isoformat(),
            "unit": None,
        },
        {
            "source_sensor_domain": "sensor",
            "name": "distance_95_percent_of_values",
            "value_0": STATE_UNKNOWN,
            "value_1": 0.0,
            "value_9": float(round(2 * 1.96 * statistics.stdev(VALUES_NUMERIC), 2)),
            "unit": "°C",
        },
        {
            "source_sensor_domain": "sensor",
            "name": "distance_99_percent_of_values",
            "value_0": STATE_UNKNOWN,
            "value_1": 0.0,
            "value_9": float(round(2 * 2.58 * statistics.stdev(VALUES_NUMERIC), 2)),
            "unit": "°C",
        },
        {
            "source_sensor_domain": "sensor",
            "name": "distance_absolute",
            "value_0": STATE_UNKNOWN,
            "value_1": float(0),
            "value_9": float(max(VALUES_NUMERIC) - min(VALUES_NUMERIC)),
            "unit": "°C",
        },
        {
            "source_sensor_domain": "sensor",
            "name": "mean",
            "value_0": STATE_UNKNOWN,
            "value_1": float(VALUES_NUMERIC[-1]),
            "value_9": float(round(sum(VALUES_NUMERIC) / len(VALUES_NUMERIC), 2)),
            "unit": "°C",
        },
        {
            "source_sensor_domain": "sensor",
            "name": "mean_circular",
            "value_0": STATE_UNKNOWN,
            "value_1": float(VALUES_NUMERIC[-1]),
            "value_9": 10.76,
            "unit": "°C",
        },
        {
            "source_sensor_domain": "sensor",
            "name": "median",
            "value_0": STATE_UNKNOWN,
            "value_1": float(VALUES_NUMERIC[-1]),
            "value_9": float(round(statistics.median(VALUES_NUMERIC), 2)),
            "unit": "°C",
        },
        {
            "source_sensor_domain": "sensor",
            "name": "noisiness",
            "value_0": STATE_UNKNOWN,
            "value_1": 0.0,
            "value_9": float(round(sum([3, 4.8, 10.2, 1.2, 5.4, 2.5, 7.3, 8]) / 8, 2)),
            "unit": "°C",
        },
        {
            "source_sensor_domain": "sensor",
            "name": "percentile",
            "value_0": STATE_UNKNOWN,
            "value_1": 6.0,
            "value_9": 9.2,
            "unit": "°C",
        },
        {
            "source_sensor_domain": "sensor",
            "name": "standard_deviation",
            "value_0": STATE_UNKNOWN,
            "value_1": 0.0,
            "value_9": float(round(statistics.stdev(VALUES_NUMERIC), 2)),
            "unit": "°C",
        },
        {
            "source_sensor_domain": "sensor",
            "name": "sum",
            "value_0": STATE_UNKNOWN,
            "value_1": float(VALUES_NUMERIC[-1]),
            "value_9": float(sum(VALUES_NUMERIC)),
            "unit": "°C",
        },
        {
            "source_sensor_domain": "sensor",
            "name": "sum_differences",
            "value_0": STATE_UNKNOWN,
            "value_1": 0.0,
            "value_9": float(
                sum(
                    [
                        abs(20 - 17),
                        abs(15.2 - 20),
                        abs(5 - 15.2),
                        abs(3.8 - 5),
                        abs(9.2 - 3.8),
                        abs(6.7 - 9.2),
                        abs(14 - 6.7),
                        abs(6 - 14),
                    ]
                )
            ),
            "unit": "°C",
        },
        {
            "source_sensor_domain": "sensor",
            "name": "sum_differences_nonnegative",
            "value_0": STATE_UNKNOWN,
            "value_1": 0.0,
            "value_9": float(
                sum(
                    [
                        20 - 17,
                        15.2 - 0,
                        5 - 0,
                        3.8 - 0,
                        9.2 - 3.8,
                        6.7 - 0,
                        14 - 6.7,
                        6 - 0,
                    ]
                )
            ),
            "unit": "°C",
        },
        {
            "source_sensor_domain": "sensor",
            "name": "total",
            "value_0": STATE_UNKNOWN,
            "value_1": float(VALUES_NUMERIC[-1]),
            "value_9": float(sum(VALUES_NUMERIC)),
            "unit": "°C",
        },
        {
            "source_sensor_domain": "sensor",
            "name": "value_max",
            "value_0": STATE_UNKNOWN,
            "value_1": float(VALUES_NUMERIC[-1]),
            "value_9": float(max(VALUES_NUMERIC)),
            "unit": "°C",
        },
        {
            "source_sensor_domain": "sensor",
            "name": "value_min",
            "value_0": STATE_UNKNOWN,
            "value_1": float(VALUES_NUMERIC[-1]),
            "value_9": float(min(VALUES_NUMERIC)),
            "unit": "°C",
        },
        {
            "source_sensor_domain": "sensor",
            "name": "variance",
            "value_0": STATE_UNKNOWN,
            "value_1": 0.0,
            "value_9": float(round(statistics.variance(VALUES_NUMERIC), 2)),
            "unit": "°C²",
        },
        {
            "source_sensor_domain": "binary_sensor",
            "name": "average_step",
            "value_0": STATE_UNKNOWN,
            "value_1": 100.0,
            "value_9": 50.0,
            "unit": "%",
        },
        {
            "source_sensor_domain": "binary_sensor",
            "name": "average_timeless",
            "value_0": STATE_UNKNOWN,
            "value_1": 100.0,
            "value_9": float(
                round(100 / len(VALUES_BINARY) * VALUES_BINARY.count("on"), 2)
            ),
            "unit": "%",
        },
        {
            "source_sensor_domain": "binary_sensor",
            "name": "count",
            "value_0": 0,
            "value_1": 1,
            "value_9": len(VALUES_BINARY),
            "unit": None,
        },
        {
            "source_sensor_domain": "binary_sensor",
            "name": "count_on",
            "value_0": 0,
            "value_1": 1,
            "value_9": VALUES_BINARY.count("on"),
            "unit": None,
        },
        {
            "source_sensor_domain": "binary_sensor",
            "name": "count_off",
            "value_0": 0,
            "value_1": 0,
            "value_9": VALUES_BINARY.count("off"),
            "unit": None,
        },
        {
            "source_sensor_domain": "binary_sensor",
            "name": "datetime_newest",
            "value_0": STATE_UNKNOWN,
            "value_1": (start_datetime + timedelta(minutes=9)).isoformat(),
            "value_9": (start_datetime + timedelta(minutes=9)).isoformat(),
            "unit": None,
        },
        {
            "source_sensor_domain": "binary_sensor",
            "name": "datetime_oldest",
            "value_0": STATE_UNKNOWN,
            "value_1": (start_datetime + timedelta(minutes=9)).isoformat(),
            "value_9": (start_datetime + timedelta(minutes=1)).isoformat(),
            "unit": None,
        },
        {
            "source_sensor_domain": "binary_sensor",
            "name": "mean",
            "value_0": STATE_UNKNOWN,
            "value_1": 100.0,
            "value_9": float(
                round(100 / len(VALUES_BINARY) * VALUES_BINARY.count("on"), 2)
            ),
            "unit": "%",
        },
    )
    sensors_config = [
        {
            "platform": "statistics",
            "name": f"test_{characteristic['source_sensor_domain']}_{characteristic['name']}",
            "entity_id": f"{characteristic['source_sensor_domain']}.test_monitored",
            "state_characteristic": characteristic["name"],
            "max_age": {"minutes": 8},  # 9 values spaces by one minute
        }
        for characteristic in characteristics
    ]

    with freeze_time(current_time) as freezer:
        assert await async_setup_component(
            hass,
            "sensor",
            {"sensor": sensors_config},
        )
        await hass.async_block_till_done()

        # With all values in buffer

        for i, value in enumerate(VALUES_NUMERIC):
            current_time += timedelta(minutes=1)
            freezer.move_to(current_time)
            async_fire_time_changed(hass, current_time)
            hass.states.async_set(
                "sensor.test_monitored",
                str(value),
                {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS},
            )
            hass.states.async_set(
                "binary_sensor.test_monitored",
                str(VALUES_BINARY[i]),
                {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS},
            )
        await hass.async_block_till_done()

        for characteristic in characteristics:
            state = hass.states.get(
                f"sensor.test_{characteristic['source_sensor_domain']}_{characteristic['name']}"
            )
            assert state is not None, (
                "no state object for characteristic "
                f"'{characteristic['source_sensor_domain']}/{characteristic['name']}' "
                "(buffer filled)"
            )
            assert state.state == str(characteristic["value_9"]), (
                "value mismatch for characteristic "
                f"'{characteristic['source_sensor_domain']}/{characteristic['name']}' "
                "(buffer filled) - "
                f"assert {state.state} == {characteristic['value_9']!s}"
            )
            assert (
                state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == characteristic["unit"]
            ), f"unit mismatch for characteristic '{characteristic['name']}'"

        # With single value in buffer

        current_time += timedelta(minutes=8)
        freezer.move_to(current_time)
        async_fire_time_changed(hass, current_time)
        await hass.async_block_till_done()

        for characteristic in characteristics:
            state = hass.states.get(
                f"sensor.test_{characteristic['source_sensor_domain']}_{characteristic['name']}"
            )
            assert state is not None, (
                "no state object for characteristic "
                f"'{characteristic['source_sensor_domain']}/{characteristic['name']}' "
                "(one stored value)"
            )
            assert state.state == str(characteristic["value_1"]), (
                "value mismatch for characteristic "
                f"'{characteristic['source_sensor_domain']}/{characteristic['name']}' "
                "(one stored value) - "
                f"assert {state.state} == {characteristic['value_1']!s}"
            )

        # With empty buffer

        current_time += timedelta(minutes=1)
        freezer.move_to(current_time)
        async_fire_time_changed(hass, current_time)
        await hass.async_block_till_done()

        for characteristic in characteristics:
            state = hass.states.get(
                f"sensor.test_{characteristic['source_sensor_domain']}_{characteristic['name']}"
            )
            assert state is not None, (
                "no state object for characteristic "
                f"'{characteristic['source_sensor_domain']}/{characteristic['name']}' "
                "(buffer empty)"
            )
            assert state.state == str(characteristic["value_0"]), (
                "value mismatch for characteristic "
                f"'{characteristic['source_sensor_domain']}/{characteristic['name']}' "
                "(buffer empty) - "
                f"assert {state.state} == {characteristic['value_0']!s}"
            )