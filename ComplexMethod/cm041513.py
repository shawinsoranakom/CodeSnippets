def test_dynamodb_stream_records_with_update_item(
        self,
        aws_client,
        dynamodb_create_table_with_parameters,
        wait_for_dynamodb_stream_ready,
        snapshot,
        dynamodbstreams_snapshot_transformers,
    ):
        table_name = f"test-ddb-table-{short_uid()}"

        create_table = dynamodb_create_table_with_parameters(
            TableName=table_name,
            KeySchema=[{"AttributeName": PARTITION_KEY, "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": PARTITION_KEY, "AttributeType": "S"}],
            ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
            StreamSpecification={"StreamEnabled": True, "StreamViewType": "NEW_AND_OLD_IMAGES"},
        )
        snapshot.match("create-table", create_table)
        stream_arn = create_table["TableDescription"]["LatestStreamArn"]
        wait_for_dynamodb_stream_ready(stream_arn=stream_arn)

        response = aws_client.dynamodbstreams.describe_stream(StreamArn=stream_arn)
        snapshot.match("describe-stream", response)
        shard_id = response["StreamDescription"]["Shards"][0]["ShardId"]
        starting_sequence_number = int(
            response["StreamDescription"]["Shards"][0]
            .get("SequenceNumberRange")
            .get("StartingSequenceNumber")
        )

        response = aws_client.dynamodbstreams.get_shard_iterator(
            StreamArn=stream_arn,
            ShardId=shard_id,
            ShardIteratorType="TRIM_HORIZON",
        )
        snapshot.match("get-shard-iterator", response)
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
        assert "ShardIterator" in response
        shard_iterator = response["ShardIterator"]

        item_id = "my-item-id"
        # assert that when we insert/update the record with the same value, no event is sent

        aws_client.dynamodb.update_item(
            TableName=table_name,
            Key={PARTITION_KEY: {"S": item_id}},
            UpdateExpression="SET attr1 = :v1, attr2 = :v2",
            ExpressionAttributeValues={
                ":v1": {"S": "value1"},
                ":v2": {"S": "value2"},
            },
        )

        def _get_item():
            res = aws_client.dynamodb.get_item(
                TableName=table_name, Key={PARTITION_KEY: {"S": item_id}}
            )
            assert res["Item"]["attr1"] == {"S": "value1"}
            assert res["Item"]["attr2"] == {"S": "value2"}

        # we need this retry to make sure the item is properly existing in DynamoDB before trying to overwrite it
        # with the same value, thus not sending the event again
        retry(_get_item, retries=3, sleep=0.1)

        # send the same update, this should not publish an event to the stream
        aws_client.dynamodb.update_item(
            TableName=table_name,
            Key={PARTITION_KEY: {"S": item_id}},
            UpdateExpression="SET attr1 = :v1, attr2 = :v2",
            ExpressionAttributeValues={
                ":v1": {"S": "value1"},
                ":v2": {"S": "value2"},
            },
        )
        # send a different update, this will trigger an `MODIFY` event
        aws_client.dynamodb.update_item(
            TableName=table_name,
            Key={PARTITION_KEY: {"S": item_id}},
            UpdateExpression="SET attr1 = :v1, attr2 = :v2",
            ExpressionAttributeValues={
                ":v1": {"S": "value2"},
                ":v2": {"S": "value3"},
            },
        )

        def _get_records_amount(record_amount: int):
            nonlocal shard_iterator

            all_records = []
            while shard_iterator is not None:
                res = aws_client.dynamodbstreams.get_records(ShardIterator=shard_iterator)
                shard_iterator = res["NextShardIterator"]
                all_records.extend(res["Records"])
                if len(all_records) >= record_amount:
                    break

            return all_records

        records = retry(lambda: _get_records_amount(2), sleep=1, retries=3)
        snapshot.match("get-records", {"Records": records})

        assert len(records) == 2
        event_insert, event_update = records
        assert isinstance(
            event_insert["dynamodb"]["ApproximateCreationDateTime"],
            datetime,
        )
        assert event_insert["dynamodb"]["ApproximateCreationDateTime"].microsecond == 0
        insert_seq_number = int(event_insert["dynamodb"]["SequenceNumber"])
        # TODO: maybe fix sequence number, seems something related to Kinesis
        if is_aws_cloud():
            assert insert_seq_number > starting_sequence_number
        else:
            assert insert_seq_number >= starting_sequence_number
        assert isinstance(
            event_update["dynamodb"]["ApproximateCreationDateTime"],
            datetime,
        )
        assert event_update["dynamodb"]["ApproximateCreationDateTime"].microsecond == 0
        assert int(event_update["dynamodb"]["SequenceNumber"]) > starting_sequence_number