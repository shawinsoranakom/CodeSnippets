def test_time_to_live(self, aws_client, ddb_test_table):
        # check response for nonexistent table
        response = testutil.send_describe_dynamodb_ttl_request("test")
        assert json.loads(response._content)["__type"] == "ResourceNotFoundException"
        assert response.status_code == 400

        response = testutil.send_update_dynamodb_ttl_request("test", True)
        assert json.loads(response._content)["__type"] == "ResourceNotFoundException"
        assert response.status_code == 400

        # Insert some items to the table
        items = {
            "id1": {PARTITION_KEY: {"S": "id1"}, "data": {"S": "IT IS"}},
            "id2": {PARTITION_KEY: {"S": "id2"}, "data": {"S": "TIME"}},
            "id3": {PARTITION_KEY: {"S": "id3"}, "data": {"S": "TO LIVE!"}},
        }

        for _, item in items.items():
            aws_client.dynamodb.put_item(TableName=ddb_test_table, Item=item)

        # Describe TTL when still unset
        response = testutil.send_describe_dynamodb_ttl_request(ddb_test_table)
        assert response.status_code == 200
        assert (
            json.loads(response._content)["TimeToLiveDescription"]["TimeToLiveStatus"] == "DISABLED"
        )

        # Enable TTL for given table
        response = testutil.send_update_dynamodb_ttl_request(ddb_test_table, True)
        assert response.status_code == 200
        assert json.loads(response._content)["TimeToLiveSpecification"]["Enabled"]

        # Describe TTL status after being enabled.
        response = testutil.send_describe_dynamodb_ttl_request(ddb_test_table)
        assert response.status_code == 200
        assert (
            json.loads(response._content)["TimeToLiveDescription"]["TimeToLiveStatus"] == "ENABLED"
        )

        # Disable TTL for given table
        response = testutil.send_update_dynamodb_ttl_request(ddb_test_table, False)
        assert response.status_code == 200
        assert not json.loads(response._content)["TimeToLiveSpecification"]["Enabled"]

        # Describe TTL status after being disabled.
        response = testutil.send_describe_dynamodb_ttl_request(ddb_test_table)
        assert response.status_code == 200
        assert (
            json.loads(response._content)["TimeToLiveDescription"]["TimeToLiveStatus"] == "DISABLED"
        )

        # Enable TTL for given table again
        response = testutil.send_update_dynamodb_ttl_request(ddb_test_table, True)
        assert response.status_code == 200
        assert json.loads(response._content)["TimeToLiveSpecification"]["Enabled"]

        # Describe TTL status after being enabled again.
        response = testutil.send_describe_dynamodb_ttl_request(ddb_test_table)
        assert response.status_code == 200
        assert (
            json.loads(response._content)["TimeToLiveDescription"]["TimeToLiveStatus"] == "ENABLED"
        )