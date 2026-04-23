def test_time_to_live_deletion(self, aws_client, ddb_test_table, cleanups):
        table_name = ddb_test_table
        # Note: we use a reserved keyboard (ttl) as an attribute name for the time to live specification to make sure
        #   that the deletion logic works also in this case.
        aws_client.dynamodb.update_time_to_live(
            TableName=table_name,
            TimeToLiveSpecification={"Enabled": True, "AttributeName": "ttl"},
        )
        aws_client.dynamodb.describe_time_to_live(TableName=table_name)

        exp = int(time.time()) - 10  # expired
        items = [
            {PARTITION_KEY: {"S": "expired"}, "ttl": {"N": str(exp)}},
            {PARTITION_KEY: {"S": "not-expired"}, "ttl": {"N": str(exp + 120)}},
        ]
        for item in items:
            aws_client.dynamodb.put_item(TableName=table_name, Item=item)

        url = f"{config.internal_service_url()}/_aws/dynamodb/expired"
        response = requests.delete(url)
        assert response.status_code == 200
        assert response.json() == {"ExpiredItems": 1}

        result = aws_client.dynamodb.get_item(
            TableName=table_name, Key={PARTITION_KEY: {"S": "not-expired"}}
        )
        assert result.get("Item")
        result = aws_client.dynamodb.get_item(
            TableName=table_name, Key={PARTITION_KEY: {"S": "expired"}}
        )
        assert not result.get("Item")

        # create a table with a range key
        table_with_range_key = f"test-table-{short_uid()}"
        aws_client.dynamodb.create_table(
            TableName=table_with_range_key,
            KeySchema=[
                {"AttributeName": "id", "KeyType": "HASH"},
                {"AttributeName": "range", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "id", "AttributeType": "S"},
                {"AttributeName": "range", "AttributeType": "S"},
            ],
            ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        )
        cleanups.append(lambda: aws_client.dynamodb.delete_table(TableName=table_with_range_key))
        aws_client.dynamodb.update_time_to_live(
            TableName=table_with_range_key,
            TimeToLiveSpecification={"Enabled": True, "AttributeName": "ttl"},
        )
        exp = int(time.time()) - 10  # expired
        items = [
            {
                PARTITION_KEY: {"S": "expired"},
                "range": {"S": "range_one"},
                "ttl": {"N": str(exp)},
            },
            {
                PARTITION_KEY: {"S": "not-expired"},
                "range": {"S": "range_two"},
                "ttl": {"N": str(exp + 120)},
            },
        ]
        for item in items:
            aws_client.dynamodb.put_item(TableName=table_with_range_key, Item=item)

        url = f"{config.internal_service_url()}/_aws/dynamodb/expired"
        response = requests.delete(url)
        assert response.status_code == 200
        assert response.json() == {"ExpiredItems": 1}

        result = aws_client.dynamodb.get_item(
            TableName=table_with_range_key,
            Key={PARTITION_KEY: {"S": "not-expired"}, "range": {"S": "range_two"}},
        )
        assert result.get("Item")
        result = aws_client.dynamodb.get_item(
            TableName=table_with_range_key,
            Key={PARTITION_KEY: {"S": "expired"}, "range": {"S": "range_one"}},
        )
        assert not result.get("Item")