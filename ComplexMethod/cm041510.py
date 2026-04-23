def test_dynamodb_with_kinesis_stream(self, aws_client):
        dynamodb = aws_client.dynamodb
        # Kinesis streams can only be in the same account and region as the table. See
        # https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/kds.html#kds_howitworks.enabling
        kinesis = aws_client.kinesis

        # create kinesis datastream
        stream_name = f"kinesis_dest_stream_{short_uid()}"
        kinesis.create_stream(StreamName=stream_name, ShardCount=1)
        # wait for the stream to be created
        sleep(1)
        # Get stream description
        stream_description = kinesis.describe_stream(StreamName=stream_name)["StreamDescription"]
        table_name = f"table_with_kinesis_stream-{short_uid()}"
        # create table
        dynamodb.create_table(
            TableName=table_name,
            KeySchema=[{"AttributeName": "Username", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "Username", "AttributeType": "S"}],
            ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        )

        # Enable kinesis destination for the table
        dynamodb.enable_kinesis_streaming_destination(
            TableName=table_name, StreamArn=stream_description["StreamARN"]
        )

        # put item into table
        dynamodb.put_item(TableName=table_name, Item={"Username": {"S": "Fred"}})

        # update item in table
        dynamodb.update_item(
            TableName=table_name,
            Key={"Username": {"S": "Fred"}},
            UpdateExpression="set S=:r",
            ExpressionAttributeValues={":r": {"S": "Fred_Modified"}},
            ReturnValues="UPDATED_NEW",
        )

        # delete item in table
        dynamodb.delete_item(TableName=table_name, Key={"Username": {"S": "Fred"}})

        def _fetch_records():
            records = queries.kinesis_get_latest_records(
                stream_name,
                shard_id=stream_description["Shards"][0]["ShardId"],
                client=kinesis,
            )
            assert len(records) == 3
            return records

        # get records from the stream
        records = retry(_fetch_records)

        for record in records:
            record = json.loads(record["Data"])
            assert record["tableName"] == table_name
            # check eventSourceARN not exists in the stream record
            assert "eventSourceARN" not in record
            if record["eventName"] == "INSERT":
                assert "OldImage" not in record["dynamodb"]
                assert "NewImage" in record["dynamodb"]
            elif record["eventName"] == "MODIFY":
                assert "NewImage" in record["dynamodb"]
                assert "OldImage" in record["dynamodb"]
            elif record["eventName"] == "REMOVE":
                assert "NewImage" not in record["dynamodb"]
                assert "OldImage" in record["dynamodb"]
        # describe kinesis streaming destination of the table
        destinations = dynamodb.describe_kinesis_streaming_destination(TableName=table_name)
        destination = destinations["KinesisDataStreamDestinations"][0]

        # assert kinesis streaming destination status
        assert stream_description["StreamARN"] == destination["StreamArn"]
        assert destination["DestinationStatus"] == "ACTIVE"

        # Disable kinesis destination
        dynamodb.disable_kinesis_streaming_destination(
            TableName=table_name, StreamArn=stream_description["StreamARN"]
        )

        # describe kinesis streaming destination of the table
        result = dynamodb.describe_kinesis_streaming_destination(TableName=table_name)
        destination = result["KinesisDataStreamDestinations"][0]

        # assert kinesis streaming destination status
        assert stream_description["StreamARN"] == destination["StreamArn"]
        assert destination["DestinationStatus"] == "DISABLED"

        # clean up
        dynamodb.delete_table(TableName=table_name)
        kinesis.delete_stream(StreamName=stream_name)