async def _async_update_data(self):
        """Update historic data via API."""
        now = dt_util.utcnow()
        self.update_interval = (
            timedelta(hours=1) + now.replace(minute=1, second=0) - now
        )

        recoder_instance = get_instance(self.hass)
        for dev_id, heater in self.mill_data_connection.devices.items():
            if not isinstance(heater, Heater):
                continue
            statistic_id = f"{DOMAIN}:energy_{slugify(dev_id)}"

            last_stats = await recoder_instance.async_add_executor_job(
                get_last_statistics, self.hass, 1, statistic_id, True, set()
            )
            if not last_stats or not last_stats.get(statistic_id):
                hourly_data = (
                    await self.mill_data_connection.fetch_historic_energy_usage(
                        dev_id, n_days=TWO_YEARS_DAYS
                    )
                )
                hourly_data = dict(sorted(hourly_data.items(), key=lambda x: x[0]))
                _sum = 0.0
                last_stats_time = None
            else:
                hourly_data = (
                    await self.mill_data_connection.fetch_historic_energy_usage(
                        dev_id,
                        n_days=(
                            now
                            - dt_util.utc_from_timestamp(
                                last_stats[statistic_id][0]["start"]
                            )
                        ).days
                        + 2,
                    )
                )
                if not hourly_data:
                    continue
                hourly_data = dict(sorted(hourly_data.items(), key=lambda x: x[0]))
                start_time = next(iter(hourly_data))
                stats = await recoder_instance.async_add_executor_job(
                    statistics_during_period,
                    self.hass,
                    start_time,
                    None,
                    {statistic_id},
                    "hour",
                    None,
                    {"sum", "state"},
                )
                stat = stats[statistic_id][0]

                _sum = cast(float, stat["sum"]) - cast(float, stat["state"])
                last_stats_time = dt_util.utc_from_timestamp(stat["start"])

            statistics = []

            for start, state in hourly_data.items():
                if state is None:
                    continue
                if (last_stats_time and start < last_stats_time) or start > now:
                    continue
                _sum += state
                statistics.append(
                    StatisticData(
                        start=start,
                        state=state,
                        sum=_sum,
                    )
                )
            metadata = StatisticMetaData(
                mean_type=StatisticMeanType.NONE,
                has_sum=True,
                name=f"{heater.name}",
                source=DOMAIN,
                statistic_id=statistic_id,
                unit_class=EnergyConverter.UNIT_CLASS,
                unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
            )
            async_add_external_statistics(self.hass, metadata, statistics)