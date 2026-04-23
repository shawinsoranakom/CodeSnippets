def test_list_tags_of_resource(self, aws_client):
        table_name = f"ddb-table-{short_uid()}"

        rs = aws_client.dynamodb.create_table(
            TableName=table_name,
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
            ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
            Tags=TEST_DDB_TAGS,
        )
        table_arn = rs["TableDescription"]["TableArn"]

        rs = aws_client.dynamodb.list_tags_of_resource(ResourceArn=table_arn)

        assert rs["Tags"] == TEST_DDB_TAGS

        aws_client.dynamodb.tag_resource(
            ResourceArn=table_arn, Tags=[{"Key": "NewKey", "Value": "TestValue"}]
        )

        rs = aws_client.dynamodb.list_tags_of_resource(ResourceArn=table_arn)

        assert len(rs["Tags"]) == len(TEST_DDB_TAGS) + 1

        tags = {tag["Key"]: tag["Value"] for tag in rs["Tags"]}
        assert "NewKey" in tags
        assert tags["NewKey"] == "TestValue"

        aws_client.dynamodb.untag_resource(ResourceArn=table_arn, TagKeys=["Name", "NewKey"])

        rs = aws_client.dynamodb.list_tags_of_resource(ResourceArn=table_arn)
        tags = {tag["Key"]: tag["Value"] for tag in rs["Tags"]}
        assert "Name" not in tags.keys()
        assert "NewKey" not in tags.keys()

        aws_client.dynamodb.delete_table(TableName=table_name)