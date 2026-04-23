def test_put_subscription_filter_kinesis(
        self, logs_log_group, logs_log_stream, create_iam_role_with_policy, aws_client
    ):
        """Test putting a subscription filter with Kinesis destination."""
        kinesis_name = f"test-kinesis-{short_uid()}"
        filter_name = "Destination"
        aws_client.kinesis.create_stream(StreamName=kinesis_name, ShardCount=1)

        try:
            result = aws_client.kinesis.describe_stream(StreamName=kinesis_name)[
                "StreamDescription"
            ]
            kinesis_arn = result["StreamARN"]
            role = f"test-kinesis-role-{short_uid()}"
            policy_name = f"test-kinesis-role-policy-{short_uid()}"
            role_arn = create_iam_role_with_policy(
                RoleName=role,
                PolicyName=policy_name,
                RoleDefinition=logs_role,
                PolicyDefinition=kinesis_permission,
            )

            # Wait for stream-status "ACTIVE"
            status = result["StreamStatus"]
            if status != "ACTIVE":

                def check_stream_active():
                    state = aws_client.kinesis.describe_stream(StreamName=kinesis_name)[
                        "StreamDescription"
                    ]["StreamStatus"]
                    if state != "ACTIVE":
                        raise Exception(f"StreamStatus is {state}")

                retry(check_stream_active, retries=6, sleep=1.0, sleep_before=2.0)

            def put_subscription_filter():
                aws_client.logs.put_subscription_filter(
                    logGroupName=logs_log_group,
                    filterName=filter_name,
                    filterPattern="",
                    destinationArn=kinesis_arn,
                    roleArn=role_arn,
                )

            retry(put_subscription_filter, retries=6, sleep=3.0)

            def put_event():
                aws_client.logs.put_log_events(
                    logGroupName=logs_log_group,
                    logStreamName=logs_log_stream,
                    logEvents=[
                        {"timestamp": now_utc(millis=True), "message": "test"},
                        {"timestamp": now_utc(millis=True), "message": "test 2"},
                    ],
                )

            retry(put_event, retries=6, sleep=3.0)

            shard_iterator = aws_client.kinesis.get_shard_iterator(
                StreamName=kinesis_name,
                ShardId="shardId-000000000000",
                ShardIteratorType="TRIM_HORIZON",
            )["ShardIterator"]

            response = aws_client.kinesis.get_records(ShardIterator=shard_iterator)
            # AWS sends messages as health checks
            assert len(response["Records"]) >= 1
            found = False
            for record in response["Records"]:
                data = record["Data"]
                unzipped_data = gzip.decompress(data)
                json_data = json.loads(unzipped_data)
                if "test" in json.dumps(json_data["logEvents"]):
                    assert len(json_data["logEvents"]) == 2
                    assert json_data["logEvents"][0]["message"] == "test"
                    assert json_data["logEvents"][1]["message"] == "test 2"
                    found = True

            assert found
        finally:
            aws_client.kinesis.delete_stream(StreamName=kinesis_name, EnforceConsumerDeletion=True)
            aws_client.logs.delete_subscription_filter(
                logGroupName=logs_log_group, filterName=filter_name
            )