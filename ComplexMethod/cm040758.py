def get_metric_statistics(
        self,
        context: RequestContext,
        namespace: Namespace,
        metric_name: MetricName,
        start_time: Timestamp,
        end_time: Timestamp,
        period: Period,
        dimensions: Dimensions = None,
        statistics: Statistics = None,
        extended_statistics: ExtendedStatistics = None,
        unit: StandardUnit = None,
        **kwargs,
    ) -> GetMetricStatisticsOutput:
        start_time_unix = int(start_time.timestamp())
        end_time_unix = int(end_time.timestamp())

        if not start_time_unix < end_time_unix:
            raise InvalidParameterValueException(
                "The parameter StartTime must be less than the parameter EndTime."
            )

        expected_datapoints = (end_time_unix - start_time_unix) / period

        if expected_datapoints > AWS_MAX_DATAPOINTS_ACCEPTED:
            raise InvalidParameterCombinationException(
                f"You have requested up to {int(expected_datapoints)} datapoints, which exceeds the limit of {AWS_MAX_DATAPOINTS_ACCEPTED}. "
                f"You may reduce the datapoints requested by increasing Period, or decreasing the time range."
            )

        stat_datapoints = {}

        units = (
            [unit]
            if unit
            else self.cloudwatch_database.get_units_for_metric_data_stat(
                account_id=context.account_id,
                region=context.region,
                start_time=start_time,
                end_time=end_time,
                metric_name=metric_name,
                namespace=namespace,
            )
        )

        for stat in statistics:
            for selected_unit in units:
                query_result = self.cloudwatch_database.get_metric_data_stat(
                    account_id=context.account_id,
                    region=context.region,
                    start_time=start_time,
                    end_time=end_time,
                    scan_by="TimestampDescending",
                    query=MetricDataQuery(
                        MetricStat=MetricStat(
                            Metric={
                                "MetricName": metric_name,
                                "Namespace": namespace,
                                "Dimensions": dimensions or [],
                            },
                            Period=period,
                            Stat=stat,
                            Unit=selected_unit,
                        )
                    ),
                )

                timestamps = query_result.get("timestamps", [])
                values = query_result.get("values", [])
                for i, timestamp in enumerate(timestamps):
                    stat_datapoints.setdefault(selected_unit, {})
                    stat_datapoints[selected_unit].setdefault(timestamp, {})
                    stat_datapoints[selected_unit][timestamp][stat] = float(values[i])
                    stat_datapoints[selected_unit][timestamp]["Unit"] = selected_unit

        datapoints: list[Datapoint] = []
        for selected_unit, results in stat_datapoints.items():
            for timestamp, stats in results.items():
                datapoints.append(
                    Datapoint(
                        Timestamp=timestamp,
                        SampleCount=stats.get("SampleCount"),
                        Average=stats.get("Average"),
                        Sum=stats.get("Sum"),
                        Minimum=stats.get("Minimum"),
                        Maximum=stats.get("Maximum"),
                        Unit="None" if selected_unit == "NULL_VALUE" else selected_unit,
                    )
                )

        return GetMetricStatisticsOutput(Datapoints=datapoints, Label=metric_name)