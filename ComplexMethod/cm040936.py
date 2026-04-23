def forward_to_kinesis_stream(
        account_id: str, region_name: str, records_map: RecordsMap
    ) -> None:
        # You can only stream data from DynamoDB to Kinesis Data Streams in the same AWS account and AWS Region as your
        # table.
        # You can only stream data from a DynamoDB table to one Kinesis data stream.
        store = get_store(account_id, region_name)

        for table_name, table_records in records_map.items():
            table_stream_type = table_records["table_stream_type"]
            if not table_stream_type.is_kinesis:
                continue

            kinesis_records = []

            table_arn = arns.dynamodb_table_arn(table_name, account_id, region_name)
            records = table_records["records"]
            table_def = store.table_definitions.get(table_name) or {}
            destinations = store.streaming_destinations.get(table_name)
            if not destinations:
                LOG.debug("Table %s has no Kinesis streaming destinations enabled", table_name)
                continue

            stream_arn = destinations[-1]["StreamArn"]
            for record in records:
                kinesis_record = dict(
                    tableName=table_name,
                    recordFormat="application/json",
                    userIdentity=None,
                    **record,
                )
                fields_to_remove = {"StreamViewType", "SequenceNumber"}
                kinesis_record["dynamodb"] = {
                    k: v for k, v in record["dynamodb"].items() if k not in fields_to_remove
                }
                kinesis_record.pop("eventVersion", None)

                hash_keys = list(
                    filter(lambda key: key["KeyType"] == "HASH", table_def["KeySchema"])
                )
                # TODO: reverse properly how AWS creates the partition key, it seems to be an MD5 hash
                kinesis_partition_key = md5(f"{table_name}{hash_keys[0]['AttributeName']}")

                kinesis_records.append(
                    {
                        "Data": json.dumps(kinesis_record, cls=BytesEncoder),
                        "PartitionKey": kinesis_partition_key,
                    }
                )

            kinesis = connect_to(
                aws_access_key_id=account_id,
                aws_secret_access_key=INTERNAL_AWS_SECRET_ACCESS_KEY,
                region_name=region_name,
            ).kinesis.request_metadata(service_principal="dynamodb", source_arn=table_arn)

            kinesis.put_records(
                StreamARN=stream_arn,
                Records=kinesis_records,
            )