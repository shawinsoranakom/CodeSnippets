def test_metric_filters_publish_to_cloudwatch(
        self, logs_log_group, logs_log_stream, aws_client
    ):
        """Test that metric filters publish metrics to CloudWatch."""
        basic_filter_name = f"test-filter-basic-{short_uid()}"
        json_filter_name = f"test-filter-json-{short_uid()}"
        namespace_name = f"test-metric-namespace-{short_uid()}"
        basic_metric_name = f"test-basic-metric-{short_uid()}"
        json_metric_name = f"test-json-metric-{short_uid()}"

        basic_transforms = {
            "metricNamespace": namespace_name,
            "metricName": basic_metric_name,
            "metricValue": "1",
            "defaultValue": 0,
        }
        json_transforms = {
            "metricNamespace": namespace_name,
            "metricName": json_metric_name,
            "metricValue": "1",
            "defaultValue": 0,
        }

        aws_client.logs.put_metric_filter(
            logGroupName=logs_log_group,
            filterName=basic_filter_name,
            filterPattern=" ",
            metricTransformations=[basic_transforms],
        )
        aws_client.logs.put_metric_filter(
            logGroupName=logs_log_group,
            filterName=json_filter_name,
            filterPattern='{$.message = "test"}',
            metricTransformations=[json_transforms],
        )

        response = aws_client.logs.describe_metric_filters(
            logGroupName=logs_log_group, filterNamePrefix="test-filter-"
        )
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
        filter_names = [_filter["filterName"] for _filter in response["metricFilters"]]
        assert basic_filter_name in filter_names
        assert json_filter_name in filter_names

        # Put log events and assert metrics being published
        events = [
            {"timestamp": now_utc(millis=True), "message": "log message 1"},
            {"timestamp": now_utc(millis=True), "message": "log message 2"},
        ]
        aws_client.logs.put_log_events(
            logGroupName=logs_log_group, logStreamName=logs_log_stream, logEvents=events
        )

        # List metrics
        def list_metrics():
            res = aws_client.cloudwatch.list_metrics(Namespace=namespace_name)
            assert len(res["Metrics"]) == 2

        retry(
            list_metrics,
            retries=20 if is_aws() else 5,
            sleep=5 if is_aws() else 1,
            sleep_before=3 if is_aws() else 0,
        )

        # Delete filters
        aws_client.logs.delete_metric_filter(
            logGroupName=logs_log_group, filterName=basic_filter_name
        )
        aws_client.logs.delete_metric_filter(
            logGroupName=logs_log_group, filterName=json_filter_name
        )

        response = aws_client.logs.describe_metric_filters(
            logGroupName=logs_log_group, filterNamePrefix="test-filter-"
        )
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
        filter_names = [_filter["filterName"] for _filter in response["metricFilters"]]
        assert basic_filter_name not in filter_names
        assert json_filter_name not in filter_names