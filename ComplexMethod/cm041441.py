def test_basic_operations_multiple_protocols(
        self, cloudwatch_http_client, aws_client, snapshot, protocol
    ):
        if is_old_provider() and protocol != "query":
            pytest.skip(
                "Skipping as Moto does not support any other protocol than `query` for CloudWatch for now"
            )
        snapshot.add_transformer(snapshot.transform.key_value("Label"))
        http_client = cloudwatch_http_client(protocol)
        response = http_client.post(
            "DescribeAlarms",
            payload={},
        )
        snapshot.match("describe-alarms", response)

        namespace1 = f"test/{short_uid()}"
        namespace2 = f"test/{short_uid()}"
        now = datetime.now(tz=UTC).replace(microsecond=0)
        start_time = now - timedelta(minutes=1)
        end_time = now + timedelta(minutes=5)

        parameters = [
            {
                "Namespace": namespace1,
                "MetricData": [{"MetricName": "someMetric", "Value": 23}],
            },
            {
                "Namespace": namespace1,
                "MetricData": [{"MetricName": "someMetric", "Value": 18}],
            },
            {
                "Namespace": namespace2,
                "MetricData": [{"MetricName": "ug", "Value": 23, "Timestamp": now}],
            },
        ]
        for index, input_values in enumerate(parameters):
            response = http_client.post_raw(
                operation="PutMetricData",
                payload=input_values,
            )
            assert response.status_code == 200
            # Check if x-amzn-RequestId is in the response headers - case-sensitive check
            assert "x-amzn-RequestId" in dict(response.headers)

        get_metric_input = {
            "MetricDataQueries": [
                {
                    "Id": "some",
                    "MetricStat": {
                        "Metric": {
                            "Namespace": namespace1,
                            "MetricName": "someMetric",
                        },
                        "Period": 60,
                        "Stat": "Sum",
                    },
                },
                {
                    "Id": "part",
                    "MetricStat": {
                        "Metric": {"Namespace": namespace2, "MetricName": "ug"},
                        "Period": 60,
                        "Stat": "Sum",
                    },
                },
            ],
            "StartTime": start_time,
            "EndTime": end_time,
        }

        def _get_metric_data_sum():
            # we can use the default AWS Client here, it is for the retries
            _response = aws_client.cloudwatch.get_metric_data(**get_metric_input)
            assert len(_response["MetricDataResults"]) == 2

            for _data_metric in _response["MetricDataResults"]:
                # TODO: there's an issue in the implementation of the service here.
                #  The returned timestamps should have the seconds set to 0
                if _data_metric["Id"] == "some":
                    assert sum(_data_metric["Values"]) == 41.0
                if _data_metric["Id"] == "part":
                    assert 23.0 == sum(_data_metric["Values"]) == 23.0

        # need to retry because the might most likely not be ingested immediately (it's fairly quick though)
        retry(_get_metric_data_sum, retries=10, sleep_before=2)

        response = http_client.post(
            operation="GetMetricData",
            payload=get_metric_input,
        )
        snapshot.match("get-metric-data", response)

        # we need special assertions for raw timestamp values, based on the protocol:
        if protocol == "query":
            timestamp = response["GetMetricDataResponse"]["GetMetricDataResult"][
                "MetricDataResults"
            ]["member"][0]["Timestamps"]["member"]
            assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", timestamp)

        elif protocol == "json":
            timestamp = response["MetricDataResults"][0]["Timestamps"][0]
            assert isinstance(timestamp, float)
            # assert this format: 1765977780.0
            assert re.match(r"^\d{10}\.0", str(timestamp))
        else:
            timestamp = response["MetricDataResults"][0]["Timestamps"][0]
            assert isinstance(timestamp, datetime)
            assert timestamp.microsecond == 0
            assert timestamp.year == now.year
            assert now.day - 1 <= timestamp.day <= now.day + 1

            # we need to decode more for CBOR, to verify we encode it the same way as AWS (datetime format + proper
            # underlying format (float)
            # See https://smithy.io/2.0/additional-specs/protocols/smithy-rpc-v2.html#timestamp-type-serialization
            # https://datatracker.ietf.org/doc/html/rfc8949.html#section-3.4
            response_raw = http_client.post_raw(
                operation="GetMetricData",
                payload=get_metric_input,
            )
            # assert that the timestamp is encoded as a Tag (6 major type) with Double of length 8
            assert b"Timestamps\x9f\xc1\xfbA" in response_raw.content