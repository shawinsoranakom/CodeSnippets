def test_global_tables_version_2019(
        self, aws_client, aws_client_factory, cleanups, dynamodb_wait_for_table_active
    ):
        # Following https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/V2globaltables.tutorial.html

        # Create clients
        dynamodb_us_east_1 = aws_client_factory(region_name="us-east-1").dynamodb
        dynamodb_eu_west_1 = aws_client_factory(region_name="eu-west-1").dynamodb
        dynamodb_ap_south_1 = aws_client_factory(region_name="ap-south-1").dynamodb
        dynamodb_sa_east_1 = aws_client_factory(region_name="sa-east-1").dynamodb

        # Create table in AP
        table_name = f"table-{short_uid()}"
        dynamodb_ap_south_1.create_table(
            TableName=table_name,
            KeySchema=[
                {"AttributeName": "Artist", "KeyType": "HASH"},
                {"AttributeName": "SongTitle", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "Artist", "AttributeType": "S"},
                {"AttributeName": "SongTitle", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        cleanups.append(lambda: dynamodb_ap_south_1.delete_table(TableName=table_name))
        dynamodb_wait_for_table_active(table_name=table_name, client=dynamodb_ap_south_1)

        # Replicate table in US and EU
        dynamodb_ap_south_1.update_table(
            TableName=table_name,
            ReplicaUpdates=[{"Create": {"RegionName": "us-east-1", "KMSMasterKeyId": "foo"}}],
        )
        dynamodb_ap_south_1.update_table(
            TableName=table_name,
            ReplicaUpdates=[{"Create": {"RegionName": "eu-west-1", "KMSMasterKeyId": "bar"}}],
        )

        # Ensure all replicas can be described
        response = dynamodb_ap_south_1.describe_table(TableName=table_name)
        assert len(response["Table"]["Replicas"]) == 2
        response = dynamodb_us_east_1.describe_table(TableName=table_name)
        assert len(response["Table"]["Replicas"]) == 2
        assert "bar" in [replica.get("KMSMasterKeyId") for replica in response["Table"]["Replicas"]]
        response = dynamodb_eu_west_1.describe_table(TableName=table_name)
        assert len(response["Table"]["Replicas"]) == 2
        assert "foo" in [replica.get("KMSMasterKeyId") for replica in response["Table"]["Replicas"]]
        with pytest.raises(Exception) as exc:
            dynamodb_sa_east_1.describe_table(TableName=table_name)
        exc.match("ResourceNotFoundException")

        # Ensure replicas can be listed everywhere
        response = dynamodb_ap_south_1.list_tables()
        assert table_name in response["TableNames"]
        response = dynamodb_us_east_1.list_tables()
        assert table_name in response["TableNames"]
        response = dynamodb_eu_west_1.list_tables()
        assert table_name in response["TableNames"]
        response = dynamodb_sa_east_1.list_tables()
        assert table_name not in response["TableNames"]

        # Put item in AP
        dynamodb_ap_south_1.put_item(
            TableName=table_name,
            Item={"Artist": {"S": "item_1"}, "SongTitle": {"S": "Song Value 1"}},
        )

        # Ensure GetItem in US and EU
        item_us_east = dynamodb_us_east_1.get_item(
            TableName=table_name,
            Key={"Artist": {"S": "item_1"}, "SongTitle": {"S": "Song Value 1"}},
        )["Item"]
        assert item_us_east
        item_eu_west = dynamodb_eu_west_1.get_item(
            TableName=table_name,
            Key={"Artist": {"S": "item_1"}, "SongTitle": {"S": "Song Value 1"}},
        )["Item"]
        assert item_eu_west

        # Ensure Scan in US and EU
        scan_us_east = dynamodb_us_east_1.scan(TableName=table_name)
        assert scan_us_east["Items"]
        scan_eu_west = dynamodb_eu_west_1.scan(TableName=table_name)
        assert scan_eu_west["Items"]

        # Ensure Query in US and EU
        query_us_east = dynamodb_us_east_1.query(
            TableName=table_name,
            KeyConditionExpression="Artist = :artist",
            ExpressionAttributeValues={":artist": {"S": "item_1"}},
        )
        assert query_us_east["Items"]
        query_eu_west = dynamodb_eu_west_1.query(
            TableName=table_name,
            KeyConditionExpression="Artist = :artist",
            ExpressionAttributeValues={":artist": {"S": "item_1"}},
        )
        assert query_eu_west["Items"]

        # Delete EU replica
        dynamodb_ap_south_1.update_table(
            TableName=table_name, ReplicaUpdates=[{"Delete": {"RegionName": "eu-west-1"}}]
        )
        with pytest.raises(Exception) as ctx:
            dynamodb_eu_west_1.get_item(
                TableName=table_name,
                Key={"Artist": {"S": "item_1"}, "SongTitle": {"S": "Song Value 1"}},
            )
        ctx.match("ResourceNotFoundException")

        # Ensure deleting a non-existent replica raises
        with pytest.raises(Exception) as exc:
            dynamodb_ap_south_1.update_table(
                TableName=table_name, ReplicaUpdates=[{"Delete": {"RegionName": "eu-west-1"}}]
            )
        exc.match(
            "Update global table operation failed because one or more replicas were not part of the global table"
        )

        # Ensure replica details are updated in other regions
        response = dynamodb_us_east_1.describe_table(TableName=table_name)
        assert len(response["Table"]["Replicas"]) == 1
        response = dynamodb_ap_south_1.describe_table(TableName=table_name)
        assert len(response["Table"]["Replicas"]) == 1

        # Ensure removing the last replica disables global table
        dynamodb_us_east_1.update_table(
            TableName=table_name, ReplicaUpdates=[{"Delete": {"RegionName": "us-east-1"}}]
        )
        response = dynamodb_ap_south_1.describe_table(TableName=table_name)
        assert "Replicas" not in response["Table"]