async def update_statistics(self) -> None:
        """Import ista EcoTrend historical statistics."""

        # Remember the statistic_id that was initially created
        # in case the entity gets renamed, because we cannot
        # change the statistic_id
        name = self.coordinator.config_entry.options.get(
            f"lts_{self.entity_description.key}_{self.consumption_unit}"
        )
        if not name:
            name = self.entity_id.removeprefix("sensor.")
            self.hass.config_entries.async_update_entry(
                entry=self.coordinator.config_entry,
                options={
                    **self.coordinator.config_entry.options,
                    f"lts_{self.entity_description.key}_{self.consumption_unit}": name,
                },
            )

        statistic_id = f"{DOMAIN}:{name}"
        statistics_sum = 0.0
        statistics_since = None

        last_stats = await get_instance(self.hass).async_add_executor_job(
            get_last_statistics,
            self.hass,
            1,
            statistic_id,
            False,
            {"sum"},
        )

        _LOGGER.debug("Last statistics: %s", last_stats)

        if last_stats:
            statistics_sum = last_stats[statistic_id][0].get("sum") or 0.0
            statistics_since = datetime.datetime.fromtimestamp(
                last_stats[statistic_id][0].get("end") or 0, tz=datetime.UTC
            ) + datetime.timedelta(days=1)

        if monthly_consumptions := get_statistics(
            self.coordinator.data[self.consumption_unit],
            self.entity_description.consumption_type,
            self.entity_description.value_type,
        ):
            statistics: list[StatisticData] = [
                {
                    "start": consumptions["date"],
                    "state": consumptions["value"],
                    "sum": (statistics_sum := statistics_sum + consumptions["value"]),
                }
                for consumptions in monthly_consumptions
                if statistics_since is None or consumptions["date"] > statistics_since
            ]

            metadata: StatisticMetaData = {
                "mean_type": StatisticMeanType.NONE,
                "has_sum": True,
                "name": f"{self.device_entry.name} {self.name}",
                "source": DOMAIN,
                "statistic_id": statistic_id,
                "unit_class": self.entity_description.unit_class,
                "unit_of_measurement": self.entity_description.native_unit_of_measurement,
            }
            if statistics:
                _LOGGER.debug("Insert statistics: %s %s", metadata, statistics)
                async_add_external_statistics(self.hass, metadata, statistics)