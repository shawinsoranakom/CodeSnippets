def get_metric_data(
        self,
        context: RequestContext,
        metric_data_queries: MetricDataQueries,
        start_time: Timestamp,
        end_time: Timestamp,
        next_token: NextToken = None,
        scan_by: ScanBy = None,
        max_datapoints: GetMetricDataMaxDatapoints = None,
        label_options: LabelOptions = None,
        **kwargs,
    ) -> GetMetricDataOutput:
        results: list[MetricDataResult] = []
        limit = max_datapoints or 100_800
        messages: MetricDataResultMessages = []
        nxt: str | None = None
        label_additions = []

        for diff in LABEL_DIFFERENTIATORS:
            non_unique = []
            for query in metric_data_queries:
                non_unique.append(query["MetricStat"][diff])
            if len(set(non_unique)) > 1:
                label_additions.append(diff)

        for query in metric_data_queries:
            query_result = self.cloudwatch_database.get_metric_data_stat(
                account_id=context.account_id,
                region=context.region,
                query=query,
                start_time=start_time,
                end_time=end_time,
                scan_by=scan_by,
            )
            if query_result.get("messages"):
                messages.extend(query_result.get("messages"))

            label = query.get("Label") or f"{query['MetricStat']['Metric']['MetricName']}"
            # TODO: does this happen even if a label is set in the query?
            for label_addition in label_additions:
                label = f"{label} {query['MetricStat'][label_addition]}"

            timestamps = query_result.get("timestamps", {})
            values = query_result.get("values", {})

            # Paginate
            timestamp_value_dicts = [
                {
                    "Timestamp": datetime.datetime.fromtimestamp(timestamp, tz=datetime.UTC),
                    "Value": float(value),
                }
                for timestamp, value in zip(timestamps, values, strict=False)
            ]

            pagination = PaginatedList(timestamp_value_dicts)
            timestamp_page, nxt = pagination.get_page(
                lambda item: str(item.get("Timestamp")),
                next_token=next_token,
                page_size=limit,
            )

            timestamps = [item.get("Timestamp") for item in timestamp_page]
            values = [item.get("Value") for item in timestamp_page]

            metric_data_result = {
                "Id": query.get("Id"),
                "Label": label,
                "StatusCode": "Complete",
                "Timestamps": timestamps,
                "Values": values,
            }
            results.append(MetricDataResult(**metric_data_result))

        return GetMetricDataOutput(MetricDataResults=results, NextToken=nxt, Messages=messages)