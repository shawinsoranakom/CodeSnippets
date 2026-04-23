def _get_from_database(
        self,
        session: Session,
        statistic_ids: set[str] | None = None,
        statistic_type: Literal["mean", "sum"] | None = None,
        statistic_source: str | None = None,
    ) -> dict[str, tuple[int, StatisticMetaData]]:
        """Fetch meta data and process it into results and/or cache."""
        # Only update the cache if we are in the recorder thread and there are no
        # new objects that are not yet committed to the database in the session.
        update_cache = (
            not session.new
            and not session.dirty
            and self.recorder.thread_id == threading.get_ident()
        )
        results: dict[str, tuple[int, StatisticMetaData]] = {}
        id_meta: tuple[int, StatisticMetaData]
        meta: StatisticMetaData
        statistic_id: str
        row_id: int
        with session.no_autoflush:
            stat_id_to_id_meta = self._stat_id_to_id_meta
            for row in execute_stmt_lambda_element(
                session,
                _generate_get_metadata_stmt(
                    statistic_ids,
                    statistic_type,
                    statistic_source,
                    self.recorder.schema_version,
                ),
                orm_rows=False,
            ):
                statistic_id = row[INDEX_STATISTIC_ID]
                row_id = row[INDEX_ID]
                if self.recorder.schema_version >= CIRCULAR_MEAN_SCHEMA_VERSION:
                    try:
                        mean_type = StatisticMeanType(row[INDEX_MEAN_TYPE])
                    except ValueError:
                        _LOGGER.warning(
                            "Invalid mean type found for statistic_id: %s, mean_type: %s. Skipping",
                            statistic_id,
                            row[INDEX_MEAN_TYPE],
                        )
                        continue
                else:
                    mean_type = (
                        StatisticMeanType.ARITHMETIC
                        if row[INDEX_MEAN_TYPE]
                        else StatisticMeanType.NONE
                    )
                if self.recorder.schema_version >= UNIT_CLASS_SCHEMA_VERSION:
                    unit_class = row[INDEX_UNIT_CLASS]
                else:
                    conv = STATISTIC_UNIT_TO_UNIT_CONVERTER.get(
                        row[INDEX_UNIT_OF_MEASUREMENT]
                    )
                    unit_class = conv.UNIT_CLASS if conv else None
                meta = {
                    "has_mean": mean_type is StatisticMeanType.ARITHMETIC,
                    "mean_type": mean_type,
                    "has_sum": row[INDEX_HAS_SUM],
                    "name": row[INDEX_NAME],
                    "source": row[INDEX_SOURCE],
                    "statistic_id": statistic_id,
                    "unit_of_measurement": row[INDEX_UNIT_OF_MEASUREMENT],
                    "unit_class": unit_class,
                }
                id_meta = (row_id, meta)
                results[statistic_id] = id_meta
                if update_cache:
                    stat_id_to_id_meta[statistic_id] = id_meta
        return results