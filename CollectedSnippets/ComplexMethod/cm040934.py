def delete_expired_items() -> int:
    """
    This utility function iterates over all stores, looks for tables with TTL enabled,
    scan such tables and delete expired items.
    """
    no_expired_items = 0
    for account_id, region_name, state in dynamodb_stores.iter_stores():
        ttl_specs = state.ttl_specifications
        client = connect_to(aws_access_key_id=account_id, region_name=region_name).dynamodb
        for table_name, ttl_spec in ttl_specs.items():
            if ttl_spec.get("Enabled", False):
                attribute_name = ttl_spec.get("AttributeName")
                current_time = int(datetime.now().timestamp())
                try:
                    result = client.scan(
                        TableName=table_name,
                        FilterExpression="#ttl <= :threshold",
                        ExpressionAttributeValues={":threshold": {"N": str(current_time)}},
                        ExpressionAttributeNames={"#ttl": attribute_name},
                    )
                    items_to_delete = result.get("Items", [])
                    no_expired_items += len(items_to_delete)
                    table_description = client.describe_table(TableName=table_name)
                    partition_key, range_key = _get_hash_and_range_key(table_description)
                    keys_to_delete = [
                        {partition_key: item.get(partition_key)}
                        if range_key is None
                        else {
                            partition_key: item.get(partition_key),
                            range_key: item.get(range_key),
                        }
                        for item in items_to_delete
                    ]
                    delete_requests = [{"DeleteRequest": {"Key": key}} for key in keys_to_delete]
                    for i in range(0, len(delete_requests), 25):
                        batch = delete_requests[i : i + 25]
                        client.batch_write_item(RequestItems={table_name: batch})
                except Exception as e:
                    LOG.warning(
                        "An error occurred when deleting expired items from table %s: %s",
                        table_name,
                        e,
                    )
    return no_expired_items