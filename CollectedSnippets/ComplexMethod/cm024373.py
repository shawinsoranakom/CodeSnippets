async def test_compile_statistics_hourly_daily_monthly_summary(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test compiling hourly statistics + monthly and daily summary."""
    dt_util.set_default_time_zone(dt_util.get_time_zone("America/Regina"))

    zero = dt_util.utcnow()
    instance = get_instance(hass)
    await async_setup_component(hass, "sensor", {})
    # Wait for the sensor recorder platform to be added
    await async_recorder_block_till_done(hass)
    attributes = {
        "device_class": None,
        "state_class": "measurement",
        "unit_of_measurement": "%",
    }

    sum_attributes = {
        "device_class": None,
        "state_class": "total",
        "unit_of_measurement": "EUR",
    }

    durations = [50, 200, 45]

    def _weighted_average(seq, i, last_state):
        total = 0
        duration = 0
        if i > 0:
            total += last_state * 5
            duration += 5
        for j, dur in enumerate(durations):
            total += seq[j] * dur
            duration += dur
        return total / duration

    def _weighted_circular_mean(
        values: Iterable[tuple[float, float]],
    ) -> tuple[float, float]:
        sin_sum = 0
        cos_sum = 0
        for x, weight in values:
            sin_sum += math.sin(x * DEG_TO_RAD) * weight
            cos_sum += math.cos(x * DEG_TO_RAD) * weight

        return (
            (RAD_TO_DEG * math.atan2(sin_sum, cos_sum)) % 360,
            math.sqrt(sin_sum**2 + cos_sum**2),
        )

    def _min(seq, last_state):
        if last_state is None:
            return min(seq)
        return min([*seq, last_state])

    def _max(seq, last_state):
        if last_state is None:
            return max(seq)
        return max([*seq, last_state])

    def _sum(seq, last_state, last_sum):
        if last_state is None:
            return seq[-1] - seq[0]
        return last_sum[-1] + seq[-1] - last_state

    # Generate states for two hours
    states = {
        "sensor.test1": [],
        "sensor.test2": [],
        "sensor.test3": [],
        "sensor.test4": [],
        "sensor.test5": [],
    }
    expected_minima = {"sensor.test1": [], "sensor.test2": [], "sensor.test3": []}
    expected_maxima = {"sensor.test1": [], "sensor.test2": [], "sensor.test3": []}
    expected_means = {
        "sensor.test1": [],
        "sensor.test2": [],
        "sensor.test3": [],
        "sensor.test5": [],
    }
    expected_states = {"sensor.test4": []}
    expected_sums = {"sensor.test4": []}
    last_states: dict[str, float | None] = {
        "sensor.test1": None,
        "sensor.test2": None,
        "sensor.test3": None,
        "sensor.test4": None,
        "sensor.test5": None,
    }
    start = zero
    for i in range(24):
        seq = [-10, 15, 30]
        # test1 has same value in every period
        four, _states = await async_record_states(
            hass, freezer, start, "sensor.test1", attributes, seq
        )
        states["sensor.test1"] += _states["sensor.test1"]
        last_state = last_states["sensor.test1"]
        expected_minima["sensor.test1"].append(_min(seq, last_state))
        expected_maxima["sensor.test1"].append(_max(seq, last_state))
        expected_means["sensor.test1"].append(_weighted_average(seq, i, last_state))
        last_states["sensor.test1"] = seq[-1]
        # test2 values change: min/max at the last state
        seq = [-10 * (i + 1), 15 * (i + 1), 30 * (i + 1)]
        four, _states = await async_record_states(
            hass, freezer, start, "sensor.test2", attributes, seq
        )
        states["sensor.test2"] += _states["sensor.test2"]
        last_state = last_states["sensor.test2"]
        expected_minima["sensor.test2"].append(_min(seq, last_state))
        expected_maxima["sensor.test2"].append(_max(seq, last_state))
        expected_means["sensor.test2"].append(_weighted_average(seq, i, last_state))
        last_states["sensor.test2"] = seq[-1]
        # test3 values change: min/max at the first state
        seq = [-10 * (23 - i + 1), 15 * (23 - i + 1), 30 * (23 - i + 1)]
        four, _states = await async_record_states(
            hass, freezer, start, "sensor.test3", attributes, seq
        )
        states["sensor.test3"] += _states["sensor.test3"]
        last_state = last_states["sensor.test3"]
        expected_minima["sensor.test3"].append(_min(seq, last_state))
        expected_maxima["sensor.test3"].append(_max(seq, last_state))
        expected_means["sensor.test3"].append(_weighted_average(seq, i, last_state))
        last_states["sensor.test3"] = seq[-1]
        # test4 values grow
        seq = [i, i + 0.5, i + 0.75]
        start_meter = start
        for j in range(len(seq)):
            _states = await async_record_meter_state(
                hass,
                freezer,
                start_meter,
                "sensor.test4",
                sum_attributes,
                seq[j : j + 1],
            )
            start_meter += timedelta(minutes=1)
            states["sensor.test4"] += _states["sensor.test4"]
        last_state = last_states["sensor.test4"]
        expected_states["sensor.test4"].append(seq[-1])
        expected_sums["sensor.test4"].append(
            _sum(seq, last_state, expected_sums["sensor.test4"])
        )
        last_states["sensor.test4"] = seq[-1]

        # test5 circular mean
        seq = [350 - i, 0 + (i / 2.0), 15 + i]
        four, _states = await async_record_states(
            hass, freezer, start, "sensor.test5", WIND_DIRECTION_ATTRIBUTES, seq
        )
        states["sensor.test5"] += _states["sensor.test5"]
        values = [(seq, durations[j]) for j, seq in enumerate(seq)]
        if (state := last_states["sensor.test5"]) is not None:
            values.append((state, 5))
        expected_means["sensor.test5"].append(_weighted_circular_mean(values))
        last_states["sensor.test5"] = seq[-1]

        start += timedelta(minutes=5)
    await async_wait_recording_done(hass)
    hist = history.get_significant_states(
        hass,
        zero - timedelta.resolution,
        four,
        hass.states.async_entity_ids(),
        significant_changes_only=False,
    )
    assert_dict_of_states_equal_without_context_and_last_changed(states, hist)
    await async_wait_recording_done(hass)

    # Generate 5-minute statistics for two hours
    start = zero
    for _ in range(24):
        do_adhoc_statistics(hass, start=start)
        await async_wait_recording_done(hass)
        start += timedelta(minutes=5)

    statistic_ids = await async_list_statistic_ids(hass)
    assert statistic_ids == [
        {
            "statistic_id": "sensor.test1",
            "display_unit_of_measurement": "%",
            "has_mean": True,
            "mean_type": StatisticMeanType.ARITHMETIC,
            "has_sum": False,
            "name": None,
            "source": "recorder",
            "statistics_unit_of_measurement": "%",
            "unit_class": "unitless",
        },
        {
            "statistic_id": "sensor.test2",
            "display_unit_of_measurement": "%",
            "has_mean": True,
            "mean_type": StatisticMeanType.ARITHMETIC,
            "has_sum": False,
            "name": None,
            "source": "recorder",
            "statistics_unit_of_measurement": "%",
            "unit_class": "unitless",
        },
        {
            "statistic_id": "sensor.test3",
            "display_unit_of_measurement": "%",
            "has_mean": True,
            "mean_type": StatisticMeanType.ARITHMETIC,
            "has_sum": False,
            "name": None,
            "source": "recorder",
            "statistics_unit_of_measurement": "%",
            "unit_class": "unitless",
        },
        {
            "statistic_id": "sensor.test4",
            "display_unit_of_measurement": "EUR",
            "has_mean": False,
            "mean_type": StatisticMeanType.NONE,
            "has_sum": True,
            "name": None,
            "source": "recorder",
            "statistics_unit_of_measurement": "EUR",
            "unit_class": None,
        },
        {
            "statistic_id": "sensor.test5",
            "display_unit_of_measurement": DEGREE,
            "has_mean": False,
            "mean_type": StatisticMeanType.CIRCULAR,
            "has_sum": False,
            "name": None,
            "source": "recorder",
            "statistics_unit_of_measurement": DEGREE,
            "unit_class": None,
        },
    ]

    # Adjust the inserted statistics
    sum_adjustment = -10
    sum_adjustement_start = zero + timedelta(minutes=65)
    for i in range(13, 24):
        expected_sums["sensor.test4"][i] += sum_adjustment
    instance.async_adjust_statistics(
        "sensor.test4", sum_adjustement_start, sum_adjustment, "EUR"
    )
    await async_wait_recording_done(hass)

    stats = statistics_during_period(hass, zero, period="5minute")
    expected_stats = {
        "sensor.test1": [],
        "sensor.test2": [],
        "sensor.test3": [],
        "sensor.test4": [],
        "sensor.test5": [],
    }
    start = zero
    end = zero + timedelta(minutes=5)
    for i in range(24):
        for entity_id, mean_extractor in (
            ("sensor.test1", lambda x: x),
            ("sensor.test2", lambda x: x),
            ("sensor.test3", lambda x: x),
            ("sensor.test4", lambda x: x),
            ("sensor.test5", lambda x: x[0]),
        ):
            expected_average = (
                mean_extractor(expected_means[entity_id][i])
                if entity_id in expected_means
                else None
            )
            expected_minimum = (
                expected_minima[entity_id][i] if entity_id in expected_minima else None
            )
            expected_maximum = (
                expected_maxima[entity_id][i] if entity_id in expected_maxima else None
            )
            expected_state = (
                expected_states[entity_id][i] if entity_id in expected_states else None
            )
            expected_sum = (
                expected_sums[entity_id][i] if entity_id in expected_sums else None
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
        start += timedelta(minutes=5)
        end += timedelta(minutes=5)
    assert stats == expected_stats

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

    verify_stats("hour", zero, lambda v: v + timedelta(hours=1))

    start = dt_util.parse_datetime("2021-08-31T06:00:00+00:00")
    assert start
    verify_stats("day", start, lambda v: v + timedelta(days=1))

    start = dt_util.parse_datetime("2021-08-01T06:00:00+00:00")
    assert start
    verify_stats("month", start, lambda v: (v + timedelta(days=31)).replace(day=1))

    assert "Error while processing event StatisticsTask" not in caplog.text