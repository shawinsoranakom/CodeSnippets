def _process_forwarded_records(
    account_id: str, region_name: str, table_name: TableName, table_records: dict, kinesis
) -> None:
    records = table_records["records"]
    stream_type = table_records["table_stream_type"]
    # if the table does not have a DynamoDB Streams enabled, skip publishing anything
    if not stream_type.stream_view_type:
        return

    # in this case, Kinesis forces the record to have both OldImage and NewImage, so we need to filter it
    # as the settings are different for DDB Streams and Kinesis
    if stream_type.is_kinesis and stream_type.stream_view_type != StreamViewType.NEW_AND_OLD_IMAGES:
        kinesis_records = []

        # StreamViewType determines what information is written to the stream for the table
        # When an item in the table is inserted, updated or deleted
        image_filter = set()
        if stream_type.stream_view_type == StreamViewType.KEYS_ONLY:
            image_filter = {"OldImage", "NewImage"}
        elif stream_type.stream_view_type == StreamViewType.OLD_IMAGE:
            image_filter = {"NewImage"}
        elif stream_type.stream_view_type == StreamViewType.NEW_IMAGE:
            image_filter = {"OldImage"}

        for record in records:
            record["dynamodb"] = {
                k: v for k, v in record["dynamodb"].items() if k not in image_filter
            }

            if "SequenceNumber" not in record["dynamodb"]:
                record["dynamodb"]["SequenceNumber"] = str(
                    get_and_increment_sequence_number_counter()
                )

            kinesis_records.append({"Data": dumps(record), "PartitionKey": "TODO"})

    else:
        kinesis_records = []
        for record in records:
            if "SequenceNumber" not in record["dynamodb"]:
                # we can mutate the record for SequenceNumber, the Kinesis forwarding takes care of filtering it
                record["dynamodb"]["SequenceNumber"] = str(
                    get_and_increment_sequence_number_counter()
                )

            # simply pass along the records, they already have the right format
            kinesis_records.append({"Data": dumps(record), "PartitionKey": "TODO"})

    stream_name = get_kinesis_stream_name(table_name)
    kinesis.put_records(
        StreamName=stream_name,
        Records=kinesis_records,
    )