def get_metric_data_stat(
        self,
        account_id: str,
        region: str,
        query: MetricDataQuery,
        start_time: datetime,
        end_time: datetime,
        scan_by: str,
    ) -> dict[str, list]:
        metric_stat = query.get("MetricStat")
        metric = metric_stat.get("Metric")
        period = metric_stat.get("Period")
        stat = metric_stat.get("Stat")
        dimensions = metric.get("Dimensions", [])
        unit = metric_stat.get("Unit")

        # prepare SQL query
        start_time_unix = self._convert_timestamp_to_unix(start_time)
        end_time_unix = self._convert_timestamp_to_unix(end_time)

        data = (
            account_id,
            region,
            metric.get("Namespace"),
            metric.get("MetricName"),
        )

        dimension_filter = "AND dimensions is null " if not dimensions else "AND dimensions LIKE ? "
        if dimensions:
            data = data + (
                self._get_ordered_dimensions_with_separator(dimensions, for_search=True),
            )

        unit_filter = ""
        if unit:
            if unit == "NULL_VALUE":
                unit_filter = "AND unit IS NULL"
            else:
                unit_filter = "AND unit = ? "
                data += (unit,)

        sql_query = f"""
        SELECT
            {STAT_TO_SQLITE_AGGREGATION_FUNC[stat]},
            SUM(count)
        FROM (
            SELECT
            value, 1 as count,
            account_id, region, metric_name, namespace, timestamp, dimensions, unit, storage_resolution
            FROM {self.TABLE_SINGLE_METRICS}
            UNION ALL
            SELECT
            {STAT_TO_SQLITE_COL_NAME_HELPER[stat]} as value, sample_count as count,
            account_id, region, metric_name, namespace, timestamp, dimensions, unit, storage_resolution
            FROM {self.TABLE_AGGREGATED_METRICS}
        ) AS combined
        WHERE account_id = ? AND region = ?
        AND namespace = ? AND metric_name = ?
        {dimension_filter}
        {unit_filter}
        AND timestamp >= ? AND timestamp < ?
        ORDER BY timestamp ASC
        """

        timestamps = []
        values = []
        query_params = []

        # Prepare all the query parameters
        while start_time_unix < end_time_unix:
            next_start_time = start_time_unix + period
            query_params.append(data + (start_time_unix, next_start_time))
            start_time_unix = next_start_time

        all_results = []
        with self.DATABASE_LOCK, sqlite3.connect(self.METRICS_DB_READ_ONLY, uri=True) as conn:
            cur = conn.cursor()
            batch_size = 500
            for i in range(0, len(query_params), batch_size):
                batch = query_params[i : i + batch_size]
                cur.execute(
                    f"""
                            SELECT * FROM (
                                {" UNION ALL ".join(["SELECT * FROM (" + sql_query + ")"] * len(batch))}
                            )
                        """,
                    sum(batch, ()),  # flatten the list of tuples in batch into a single tuple
                )
                all_results.extend(cur.fetchall())

        # Process results outside the lock
        for i, result_row in enumerate(all_results):
            if result_row[1]:
                calculated_result = (
                    result_row[0] / result_row[1] if stat == "Average" else result_row[0]
                )
                timestamps.append(query_params[i][-2])  # start_time_unix
                values.append(calculated_result)

        # The while loop while always give us the timestamps in ascending order as we start with the start_time
        # and increase it by the period until we reach the end_time
        # If we want the timestamps in descending order we need to reverse the list
        if scan_by is None or scan_by == ScanBy.TimestampDescending:
            timestamps = timestamps[::-1]
            values = values[::-1]

        return {
            "timestamps": timestamps,
            "values": values,
        }