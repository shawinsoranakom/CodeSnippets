def test_stream_spec_and_region_replacement(self, aws_client, region_name):
        # our V1 and V2 implementation are pretty different, and we need different ways to test it
        ddbstreams = aws_client.dynamodbstreams
        table_name = f"ddb-{short_uid()}"
        resources.create_dynamodb_table(
            table_name,
            partition_key=PARTITION_KEY,
            stream_view_type="NEW_AND_OLD_IMAGES",
            client=aws_client.dynamodb,
        )

        table = aws_client.dynamodb.describe_table(TableName=table_name)["Table"]

        # assert ARN formats
        expected_arn_prefix = f"arn:aws:dynamodb:{region_name}"
        assert table["TableArn"].startswith(expected_arn_prefix)
        assert table["LatestStreamArn"].startswith(expected_arn_prefix)

        # test list_streams filtering
        stream_tables = ddbstreams.list_streams(TableName="foo")["Streams"]
        assert len(stream_tables) == 0

        if not config.DDB_STREAMS_PROVIDER_V2:
            from localstack.services.dynamodbstreams.dynamodbstreams_api import (
                get_kinesis_stream_name,
            )

            stream_name = get_kinesis_stream_name(table_name)
            assert stream_name in aws_client.kinesis.list_streams()["StreamNames"]

        # assert stream has been created
        stream_tables = [
            s["TableName"] for s in ddbstreams.list_streams(TableName=table_name)["Streams"]
        ]
        assert table_name in stream_tables
        assert len(stream_tables) == 1

        # assert shard ID formats
        result = ddbstreams.describe_stream(StreamArn=table["LatestStreamArn"])["StreamDescription"]
        assert "Shards" in result
        for shard in result["Shards"]:
            assert re.match(r"^shardId-[0-9]{20}-[a-zA-Z0-9]{1,36}$", shard["ShardId"])

        # clean up
        aws_client.dynamodb.delete_table(TableName=table_name)

        def _assert_stream_disabled():
            if config.DDB_STREAMS_PROVIDER_V2:
                _result = aws_client.dynamodbstreams.describe_stream(
                    StreamArn=table["LatestStreamArn"]
                )
                assert _result["StreamDescription"]["StreamStatus"] == "DISABLED"
            else:
                _stream_tables = [s["TableName"] for s in ddbstreams.list_streams()["Streams"]]
                assert table_name not in _stream_tables
                assert stream_name not in aws_client.kinesis.list_streams()["StreamNames"]

        # assert stream has been deleted
        retry(_assert_stream_disabled, sleep=1, retries=20)