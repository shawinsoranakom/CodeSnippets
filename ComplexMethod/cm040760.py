def add_metric_data(
        self, account_id: str, region: str, namespace: str, metric_data: MetricData
    ):
        def _get_current_unix_timestamp_utc():
            now = datetime.utcnow().replace(tzinfo=UTC)
            return int(now.timestamp())

        for metric in metric_data:
            unix_timestamp = (
                self._convert_timestamp_to_unix(metric.get("Timestamp"))
                if metric.get("Timestamp")
                else _get_current_unix_timestamp_utc()
            )

            inserts = []
            if metric.get("Value") is not None:
                inserts.append({"Value": metric.get("Value"), "TimesToInsert": 1})
            elif metric.get("Values"):
                counts = metric.get("Counts", [1] * len(metric.get("Values")))
                inserts = [
                    {"Value": value, "TimesToInsert": int(counts[indexValue])}
                    for indexValue, value in enumerate(metric.get("Values"))
                ]
            all_data = []
            for insert in inserts:
                times_to_insert = insert.get("TimesToInsert")

                data = (
                    account_id,
                    region,
                    metric.get("MetricName"),
                    namespace,
                    unix_timestamp,
                    self._get_ordered_dimensions_with_separator(metric.get("Dimensions")),
                    metric.get("Unit"),
                    metric.get("StorageResolution"),
                    insert.get("Value"),
                )
                all_data.extend([data] * times_to_insert)

            if all_data:
                with self.DATABASE_LOCK, sqlite3.connect(self.METRICS_DB) as conn:
                    cur = conn.cursor()
                    query = f"INSERT INTO {self.TABLE_SINGLE_METRICS} (account_id, region, metric_name, namespace, timestamp, dimensions, unit, storage_resolution, value) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
                    cur.executemany(query, all_data)
                    conn.commit()

            if statistic_values := metric.get("StatisticValues"):
                with self.DATABASE_LOCK, sqlite3.connect(self.METRICS_DB) as conn:
                    cur = conn.cursor()
                    cur.execute(
                        f"""INSERT INTO {self.TABLE_AGGREGATED_METRICS}
                    ("account_id", "region", "metric_name", "namespace", "timestamp", "dimensions", "unit", "storage_resolution", "sample_count", "sum", "min", "max")
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            account_id,
                            region,
                            metric.get("MetricName"),
                            namespace,
                            unix_timestamp,
                            self._get_ordered_dimensions_with_separator(metric.get("Dimensions")),
                            metric.get("Unit"),
                            metric.get("StorageResolution"),
                            statistic_values.get("SampleCount"),
                            statistic_values.get("Sum"),
                            statistic_values.get("Minimum"),
                            statistic_values.get("Maximum"),
                        ),
                    )

                    conn.commit()