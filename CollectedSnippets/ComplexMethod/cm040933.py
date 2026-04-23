def find_existing_items(
        put_items_per_table: dict[
            TableName, list[PutRequest | DeleteRequest | Put | Update | Delete]
        ],
        account_id: str,
        region_name: str,
        endpoint_url: str,
    ) -> BatchGetResponseMap:
        from localstack.services.dynamodb.provider import ValidationException

        ddb_client = ItemFinder.get_ddb_local_client(account_id, region_name, endpoint_url)

        get_items_request: BatchGetRequestMap = {}
        for table_name, put_item_reqs in put_items_per_table.items():
            table_schema = None
            for put_item in put_item_reqs:
                search_key = {}
                if "Key" in put_item:
                    search_key = put_item["Key"]
                else:
                    if not table_schema:
                        table_schema = SchemaExtractor.get_table_schema(
                            table_name, account_id, region_name
                        )

                    schemas = [table_schema["Table"]["KeySchema"]]
                    for index in table_schema["Table"].get("GlobalSecondaryIndexes", []):
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
                        continue
                table_keys = get_items_request.setdefault(table_name, {"Keys": []})
                table_keys["Keys"].append(search_key)

        try:
            existing_items = ddb_client.batch_get_item(RequestItems=get_items_request)
        except ddb_client.exceptions.ClientError as e:
            LOG.warning(
                "Unable to get items from DynamoDB tables '%s': %s",
                list(put_items_per_table.values()),
                e,
            )
            return {}

        return existing_items.get("Responses", {})