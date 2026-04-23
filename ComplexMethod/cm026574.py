async def _insert_statistics(self) -> None:
        """Insert Tibber statistics."""
        tibber_connection = await self._async_get_client()
        for home in tibber_connection.get_homes():
            sensors: list[tuple[str, bool, str | None, str]] = []
            if home.hourly_consumption_data:
                sensors.append(
                    (
                        "consumption",
                        False,
                        EnergyConverter.UNIT_CLASS,
                        UnitOfEnergy.KILO_WATT_HOUR,
                    )
                )
                sensors.append(("totalCost", False, None, home.currency))
            if home.hourly_production_data:
                sensors.append(
                    (
                        "production",
                        True,
                        EnergyConverter.UNIT_CLASS,
                        UnitOfEnergy.KILO_WATT_HOUR,
                    )
                )
                sensors.append(("profit", True, None, home.currency))

            for sensor_type, is_production, unit_class, unit in sensors:
                statistic_id = (
                    f"{DOMAIN}:energy_"
                    f"{sensor_type.lower()}_"
                    f"{home.home_id.replace('-', '')}"
                )

                last_stats = await get_instance(self.hass).async_add_executor_job(
                    get_last_statistics, self.hass, 1, statistic_id, True, set()
                )

                if not last_stats:
                    # First time we insert 5 years of data (if available)
                    hourly_data = await home.get_historic_data(
                        5 * 365 * 24, production=is_production
                    )

                    _sum = 0.0
                    last_stats_time = None
                else:
                    # hourly_consumption/production_data contains the last 30 days
                    # of consumption/production data.
                    # We update the statistics with the last 30 days
                    # of data to handle corrections in the data.
                    hourly_data = (
                        home.hourly_production_data
                        if is_production
                        else home.hourly_consumption_data
                    )

                    from_time = dt_util.parse_datetime(hourly_data[0]["from"])
                    if from_time is None:
                        continue
                    start = from_time - timedelta(hours=1)
                    stat = await get_instance(self.hass).async_add_executor_job(
                        statistics_during_period,
                        self.hass,
                        start,
                        None,
                        {statistic_id},
                        "hour",
                        None,
                        {"sum"},
                    )
                    if statistic_id in stat:
                        first_stat = stat[statistic_id][0]
                        _sum = cast(float, first_stat["sum"])
                        last_stats_time = first_stat["start"]
                    else:
                        hourly_data = await home.get_historic_data(
                            FIVE_YEARS, production=is_production
                        )
                        _sum = 0.0
                        last_stats_time = None

                statistics = []

                last_stats_time_dt = (
                    dt_util.utc_from_timestamp(last_stats_time)
                    if last_stats_time
                    else None
                )

                for data in hourly_data:
                    if data.get(sensor_type) is None:
                        continue

                    from_time = dt_util.parse_datetime(data["from"])
                    if from_time is None or (
                        last_stats_time_dt is not None
                        and from_time <= last_stats_time_dt
                    ):
                        continue

                    _sum += data[sensor_type]

                    statistics.append(
                        StatisticData(
                            start=from_time,
                            state=data[sensor_type],
                            sum=_sum,
                        )
                    )

                metadata = StatisticMetaData(
                    mean_type=StatisticMeanType.NONE,
                    has_sum=True,
                    name=f"{home.name} {sensor_type}",
                    source=DOMAIN,
                    statistic_id=statistic_id,
                    unit_class=unit_class,
                    unit_of_measurement=unit,
                )
                async_add_external_statistics(self.hass, metadata, statistics)