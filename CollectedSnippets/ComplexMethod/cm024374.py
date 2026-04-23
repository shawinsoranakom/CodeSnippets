def verify_stats(
        period: Literal["hour", "day", "week", "month"],
        start: datetime,
        next_datetime: Callable[[datetime], datetime],
    ) -> None:
        stats = statistics_during_period(hass, zero, period=period)
        expected_stats = {
            "sensor.test1": [],
            "sensor.test2": [],
            "sensor.test3": [],
            "sensor.test4": [],
            "sensor.test5": [],
        }
        end = next_datetime(start)
        for i in range(2):
            for entity_id, mean_fn in (
                ("sensor.test1", mean),
                ("sensor.test2", mean),
                ("sensor.test3", mean),
                ("sensor.test4", mean),
                ("sensor.test5", lambda x: _weighted_circular_mean(x)[0]),
            ):
                expected_average = (
                    mean_fn(expected_means[entity_id][i * 12 : (i + 1) * 12])
                    if entity_id in expected_means
                    else None
                )
                expected_minimum = (
                    min(expected_minima[entity_id][i * 12 : (i + 1) * 12])
                    if entity_id in expected_minima
                    else None
                )
                expected_maximum = (
                    max(expected_maxima[entity_id][i * 12 : (i + 1) * 12])
                    if entity_id in expected_maxima
                    else None
                )
                expected_state = (
                    expected_states[entity_id][(i + 1) * 12 - 1]
                    if entity_id in expected_states
                    else None
                )
                expected_sum = (
                    expected_sums[entity_id][(i + 1) * 12 - 1]
                    if entity_id in expected_sums
                    else None
                )
                expected_stats[entity_id].append(
                    {
                        "start": process_timestamp(start).timestamp(),
                        "end": process_timestamp(end).timestamp(),
                        "mean": pytest.approx(expected_average),
                        "min": pytest.approx(expected_minimum),
                        "max": pytest.approx(expected_maximum),
                        "last_reset": None,
                        "state": expected_state,
                        "sum": expected_sum,
                    }
                )
            start = next_datetime(start)
            end = next_datetime(end)
        assert stats == expected_stats