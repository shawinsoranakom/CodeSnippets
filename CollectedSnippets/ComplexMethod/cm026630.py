async def ws_get_fossil_energy_consumption(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Calculate amount of fossil based energy."""
    start_time_str = msg["start_time"]
    end_time_str = msg["end_time"]

    if start_time := dt_util.parse_datetime(start_time_str):
        start_time = dt_util.as_utc(start_time)
    else:
        connection.send_error(msg["id"], "invalid_start_time", "Invalid start_time")
        return

    if end_time := dt_util.parse_datetime(end_time_str):
        end_time = dt_util.as_utc(end_time)
    else:
        connection.send_error(msg["id"], "invalid_end_time", "Invalid end_time")
        return

    statistic_ids = set(msg["energy_statistic_ids"])
    statistic_ids.add(msg["co2_statistic_id"])

    # Fetch energy + CO2 statistics
    statistics = await recorder.get_instance(hass).async_add_executor_job(
        recorder.statistics.statistics_during_period,
        hass,
        start_time,
        end_time,
        statistic_ids,
        "hour",
        {"energy": UnitOfEnergy.KILO_WATT_HOUR},
        {"mean", "change"},
    )

    def _combine_change_statistics(
        stats: dict[str, list[StatisticsRow]], statistic_ids: list[str]
    ) -> dict[float, float]:
        """Combine multiple statistics, returns a dict indexed by start time."""
        result: defaultdict[float, float] = defaultdict(float)

        for statistics_id, stat in stats.items():
            if statistics_id not in statistic_ids:
                continue
            for period in stat:
                if (change := period.get("change")) is None:
                    continue
                result[period["start"]] += change

        return {key: result[key] for key in sorted(result)}

    def _reduce_deltas(
        stat_list: list[dict[str, Any]],
        same_period: Callable[[float, float], bool],
        period_start_end: Callable[[float], tuple[float, float]],
        period: timedelta,
    ) -> list[dict[str, Any]]:
        """Reduce hourly deltas to daily or monthly deltas."""
        result: list[dict[str, Any]] = []
        deltas: list[float] = []
        if not stat_list:
            return result
        prev_stat: dict[str, Any] = stat_list[0]
        fake_stat = {"start": stat_list[-1]["start"] + period.total_seconds()}

        # Loop over the hourly deltas + a fake entry to end the period
        for statistic in chain(stat_list, (fake_stat,)):
            if not same_period(prev_stat["start"], statistic["start"]):
                start, _ = period_start_end(prev_stat["start"])
                # The previous statistic was the last entry of the period
                result.append(
                    {
                        "start": dt_util.utc_from_timestamp(start).isoformat(),
                        "delta": sum(deltas),
                    }
                )
                deltas = []
            if statistic.get("delta") is not None:
                deltas.append(statistic["delta"])
            prev_stat = statistic

        return result

    merged_energy_statistics = _combine_change_statistics(
        statistics, msg["energy_statistic_ids"]
    )
    indexed_co2_statistics = cast(
        dict[float, float],
        {
            period["start"]: period["mean"]
            for period in statistics.get(msg["co2_statistic_id"], {})
        },
    )

    # Calculate amount of fossil based energy, assume 100% fossil if missing
    fossil_energy = [
        {"start": start, "delta": delta * indexed_co2_statistics.get(start, 100) / 100}
        for start, delta in merged_energy_statistics.items()
    ]

    if msg["period"] == "hour":
        reduced_fossil_energy = [
            {
                "start": dt_util.utc_from_timestamp(period["start"]).isoformat(),
                "delta": period["delta"],
            }
            for period in fossil_energy
        ]

    elif msg["period"] == "day":
        _same_day_ts, _day_start_end_ts = recorder.statistics.reduce_day_ts_factory()
        reduced_fossil_energy = _reduce_deltas(
            fossil_energy,
            _same_day_ts,
            _day_start_end_ts,
            timedelta(days=1),
        )
    else:
        (
            _same_month_ts,
            _month_start_end_ts,
        ) = recorder.statistics.reduce_month_ts_factory()
        reduced_fossil_energy = _reduce_deltas(
            fossil_energy,
            _same_month_ts,
            _month_start_end_ts,
            timedelta(days=1),
        )

    result = {period["start"]: period["delta"] for period in reduced_fossil_energy}
    connection.send_result(msg["id"], result)