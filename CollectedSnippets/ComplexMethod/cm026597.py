async def _async_maybe_migrate_statistics(
        self,
        utility_account_id: str,
        migration_map: dict[str, str],
        metadata_map: dict[str, StatisticMetaData],
    ) -> bool:
        """Perform one-time statistics migration based on the provided map.

        Splits negative values from source IDs into target IDs.

        Args:
            utility_account_id: The account ID (for issue_id).
            migration_map: Map from source statistic ID to target statistic ID
                           (e.g., {cost_id: compensation_id}).
            metadata_map: Map of all statistic IDs (source and target) to their metadata.

        """
        if not migration_map:
            return False

        need_migration_source_ids = set()
        for source_id, target_id in migration_map.items():
            last_target_stat = await get_instance(self.hass).async_add_executor_job(
                get_last_statistics,
                self.hass,
                1,
                target_id,
                True,
                set(),
            )
            if not last_target_stat:
                need_migration_source_ids.add(source_id)
        if not need_migration_source_ids:
            return False

        _LOGGER.info("Starting one-time migration for: %s", need_migration_source_ids)

        processed_stats: dict[str, list[StatisticData]] = {}

        existing_stats = await get_instance(self.hass).async_add_executor_job(
            statistics_during_period,
            self.hass,
            dt_util.utc_from_timestamp(0),
            None,
            need_migration_source_ids,
            "hour",
            None,
            {"start", "state", "sum"},
        )
        for source_id, source_stats in existing_stats.items():
            _LOGGER.debug("Found %d statistics for %s", len(source_stats), source_id)
            if not source_stats:
                need_migration_source_ids.remove(source_id)
                continue
            target_id = migration_map[source_id]

            updated_source_stats: list[StatisticData] = []
            new_target_stats: list[StatisticData] = []
            updated_source_sum = 0.0
            new_target_sum = 0.0
            need_migration = False

            prev_sum = 0.0
            for stat in source_stats:
                start = dt_util.utc_from_timestamp(stat["start"])
                curr_sum = cast(float, stat["sum"])
                state = curr_sum - prev_sum
                prev_sum = curr_sum
                if state < 0:
                    need_migration = True

                updated_source_state = max(0, state)
                new_target_state = max(0, -state)

                updated_source_sum += updated_source_state
                new_target_sum += new_target_state

                updated_source_stats.append(
                    StatisticData(
                        start=start, state=updated_source_state, sum=updated_source_sum
                    )
                )
                new_target_stats.append(
                    StatisticData(
                        start=start, state=new_target_state, sum=new_target_sum
                    )
                )

            if need_migration:
                processed_stats[source_id] = updated_source_stats
                processed_stats[target_id] = new_target_stats
            else:
                need_migration_source_ids.remove(source_id)

        if not need_migration_source_ids:
            _LOGGER.debug("No migration needed")
            return False

        for stat_id, stats in processed_stats.items():
            _LOGGER.debug("Applying %d migrated stats for %s", len(stats), stat_id)
            async_add_external_statistics(self.hass, metadata_map[stat_id], stats)

        ir.async_create_issue(
            self.hass,
            DOMAIN,
            issue_id=f"return_to_grid_migration_{utility_account_id}",
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key="return_to_grid_migration",
            translation_placeholders={
                "utility_account_id": utility_account_id,
                "energy_settings": "/config/energy",
                "target_ids": "\n".join(
                    {
                        str(metadata_map[v]["name"])
                        for k, v in migration_map.items()
                        if k in need_migration_source_ids
                    }
                ),
            },
        )

        return True