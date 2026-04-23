async def _insert_statistics(self, accounts: list[Account]) -> dict[str, datetime]:
        """Insert Opower statistics."""
        last_changed_per_account: dict[str, datetime] = {}
        for account in accounts:
            id_prefix = (
                (
                    f"{self.api.utility.subdomain()}_{account.meter_type.name}_"
                    f"{account.utility_account_id}"
                )
                # Some utilities like AEP have "-" in their account id.
                # Other utilities like ngny-gas have "-" in their subdomain.
                # Replace it with "_" to avoid "Invalid statistic_id"
                .replace("-", "_")
                .lower()
            )
            cost_statistic_id = f"{DOMAIN}:{id_prefix}_energy_cost"
            compensation_statistic_id = f"{DOMAIN}:{id_prefix}_energy_compensation"
            consumption_statistic_id = f"{DOMAIN}:{id_prefix}_energy_consumption"
            return_statistic_id = f"{DOMAIN}:{id_prefix}_energy_return"
            _LOGGER.debug(
                "Updating Statistics for %s, %s, %s, and %s",
                cost_statistic_id,
                compensation_statistic_id,
                consumption_statistic_id,
                return_statistic_id,
            )

            name_prefix = (
                f"Opower {self.api.utility.subdomain()} "
                f"{account.meter_type.name.lower()} {account.utility_account_id}"
            )
            cost_metadata = StatisticMetaData(
                mean_type=StatisticMeanType.NONE,
                has_sum=True,
                name=f"{name_prefix} cost",
                source=DOMAIN,
                statistic_id=cost_statistic_id,
                unit_class=None,
                unit_of_measurement=None,
            )
            compensation_metadata = StatisticMetaData(
                mean_type=StatisticMeanType.NONE,
                has_sum=True,
                name=f"{name_prefix} compensation",
                source=DOMAIN,
                statistic_id=compensation_statistic_id,
                unit_class=None,
                unit_of_measurement=None,
            )
            consumption_unit_class = (
                EnergyConverter.UNIT_CLASS
                if account.meter_type == MeterType.ELEC
                else VolumeConverter.UNIT_CLASS
            )
            consumption_unit = (
                UnitOfEnergy.KILO_WATT_HOUR
                if account.meter_type == MeterType.ELEC
                else UnitOfVolume.CENTUM_CUBIC_FEET
            )
            consumption_metadata = StatisticMetaData(
                mean_type=StatisticMeanType.NONE,
                has_sum=True,
                name=f"{name_prefix} consumption",
                source=DOMAIN,
                statistic_id=consumption_statistic_id,
                unit_class=consumption_unit_class,
                unit_of_measurement=consumption_unit,
            )
            return_metadata = StatisticMetaData(
                mean_type=StatisticMeanType.NONE,
                has_sum=True,
                name=f"{name_prefix} return",
                source=DOMAIN,
                statistic_id=return_statistic_id,
                unit_class=consumption_unit_class,
                unit_of_measurement=consumption_unit,
            )

            last_stat = await get_instance(self.hass).async_add_executor_job(
                get_last_statistics, self.hass, 1, consumption_statistic_id, True, set()
            )
            if not last_stat:
                _LOGGER.debug("Updating statistic for the first time")
                cost_reads = await self._async_get_cost_reads(
                    account, self.api.utility.timezone()
                )
                cost_sum = 0.0
                compensation_sum = 0.0
                consumption_sum = 0.0
                return_sum = 0.0
                last_stats_time = None
            else:
                migrated = await self._async_maybe_migrate_statistics(
                    account.utility_account_id,
                    {
                        cost_statistic_id: compensation_statistic_id,
                        consumption_statistic_id: return_statistic_id,
                    },
                    {
                        cost_statistic_id: cost_metadata,
                        compensation_statistic_id: compensation_metadata,
                        consumption_statistic_id: consumption_metadata,
                        return_statistic_id: return_metadata,
                    },
                )
                if migrated:
                    # Skip update to avoid working on old data since the migration is done
                    # asynchronously. Update the statistics in the next refresh in 12h.
                    _LOGGER.debug(
                        "Statistics migration completed. Skipping update for now"
                    )
                    continue
                cost_reads = await self._async_get_cost_reads(
                    account,
                    self.api.utility.timezone(),
                    last_stat[consumption_statistic_id][0]["start"],
                )
                if not cost_reads:
                    _LOGGER.debug("No recent usage/cost data. Skipping update")
                    continue
                start = cost_reads[0].start_time
                _LOGGER.debug("Getting statistics at: %s", start)
                # In the common case there should be a previous statistic at start time
                # so we only need to fetch one statistic. If there isn't any, fetch all.
                for end in (start + timedelta(seconds=1), None):
                    stats = await get_instance(self.hass).async_add_executor_job(
                        statistics_during_period,
                        self.hass,
                        start,
                        end,
                        {
                            cost_statistic_id,
                            compensation_statistic_id,
                            consumption_statistic_id,
                            return_statistic_id,
                        },
                        "hour",
                        None,
                        {"sum"},
                    )
                    if stats:
                        break
                    if end:
                        _LOGGER.debug(
                            "Not found. Trying to find the oldest statistic after %s",
                            start,
                        )
                # We are in this code path only if get_last_statistics found a stat
                # so statistics_during_period should also have found at least one.
                assert stats

                def _safe_get_sum(records: list[Any]) -> float:
                    if records and "sum" in records[0]:
                        return float(records[0]["sum"])
                    return 0.0

                cost_sum = _safe_get_sum(stats.get(cost_statistic_id, []))
                compensation_sum = _safe_get_sum(
                    stats.get(compensation_statistic_id, [])
                )
                consumption_sum = _safe_get_sum(stats.get(consumption_statistic_id, []))
                return_sum = _safe_get_sum(stats.get(return_statistic_id, []))
                last_stats_time = stats[consumption_statistic_id][0]["start"]

            if cost_reads:
                last_changed_per_account[account.utility_account_id] = cost_reads[
                    -1
                ].start_time
            elif last_stats_time is not None:
                last_changed_per_account[account.utility_account_id] = (
                    dt_util.utc_from_timestamp(last_stats_time)
                )

            cost_statistics = []
            compensation_statistics = []
            consumption_statistics = []
            return_statistics = []

            for cost_read in cost_reads:
                start = cost_read.start_time
                if last_stats_time is not None and start.timestamp() <= last_stats_time:
                    continue

                cost_state = max(0, cost_read.provided_cost)
                compensation_state = max(0, -cost_read.provided_cost)
                consumption_state = max(0, cost_read.consumption)
                return_state = max(0, -cost_read.consumption)

                cost_sum += cost_state
                compensation_sum += compensation_state
                consumption_sum += consumption_state
                return_sum += return_state

                cost_statistics.append(
                    StatisticData(start=start, state=cost_state, sum=cost_sum)
                )
                compensation_statistics.append(
                    StatisticData(
                        start=start, state=compensation_state, sum=compensation_sum
                    )
                )
                consumption_statistics.append(
                    StatisticData(
                        start=start, state=consumption_state, sum=consumption_sum
                    )
                )
                return_statistics.append(
                    StatisticData(start=start, state=return_state, sum=return_sum)
                )

            _LOGGER.debug(
                "Adding %s statistics for %s",
                len(cost_statistics),
                cost_statistic_id,
            )
            async_add_external_statistics(self.hass, cost_metadata, cost_statistics)
            _LOGGER.debug(
                "Adding %s statistics for %s",
                len(compensation_statistics),
                compensation_statistic_id,
            )
            async_add_external_statistics(
                self.hass, compensation_metadata, compensation_statistics
            )
            _LOGGER.debug(
                "Adding %s statistics for %s",
                len(consumption_statistics),
                consumption_statistic_id,
            )
            async_add_external_statistics(
                self.hass, consumption_metadata, consumption_statistics
            )
            _LOGGER.debug(
                "Adding %s statistics for %s",
                len(return_statistics),
                return_statistic_id,
            )
            async_add_external_statistics(self.hass, return_metadata, return_statistics)

        return last_changed_per_account