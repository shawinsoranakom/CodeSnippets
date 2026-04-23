def find_existing_item(
        put_item: dict,
        table_name: str,
        account_id: str,
        region_name: str,
        endpoint_url: str,
    ) -> AttributeMap | None:
        from localstack.services.dynamodb.provider import ValidationException

        ddb_client = ItemFinder.get_ddb_local_client(account_id, region_name, endpoint_url)

        search_key = {}
        if "Key" in put_item:
            search_key = put_item["Key"]
        else:
            schema = SchemaExtractor.get_table_schema(table_name, account_id, region_name)
            schemas = [schema["Table"]["KeySchema"]]
            for index in schema["Table"].get("GlobalSecondaryIndexes", []):
                # TODO
                # schemas.append(index['KeySchema'])
                pass
            for schema in schemas:
                for key in schema:
                    key_name = key["AttributeName"]
                    key_value = put_item["Item"].get(key_name)
                    if not key_value:
                        raise ValidationException(
                            "The provided key element does not match the schema"
                        )
                    search_key[key_name] = key_value
            if not search_key:
                return

        try:
            existing_item = ddb_client.get_item(TableName=table_name, Key=search_key)
        except ddb_client.exceptions.ClientError as e:
            LOG.warning(
                "Unable to get item from DynamoDB table '%s': %s",
                table_name,
                e,
            )
            return

        return existing_item.get("Item")