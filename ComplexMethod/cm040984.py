def describe_stream(
        self,
        context: RequestContext,
        stream_arn: StreamArn,
        limit: PositiveIntegerObject | None = None,
        exclusive_start_shard_id: ShardId | None = None,
        shard_filter: ShardFilter | None = None,
        **kwargs,
    ) -> DescribeStreamOutput:
        # TODO add support for shard_filter
        og_region = get_original_region(context=context, stream_arn=stream_arn)
        store = get_dynamodbstreams_store(context.account_id, og_region)
        kinesis = get_kinesis_client(account_id=context.account_id, region_name=og_region)
        for stream in store.ddb_streams.values():
            stream_description = stream.StreamDescription
            _stream_arn = stream_arn
            if context.region != og_region:
                _stream_arn = change_region_in_ddb_stream_arn(_stream_arn, og_region)
            if stream_description["StreamArn"] == _stream_arn:
                # get stream details
                dynamodb = connect_to(
                    aws_access_key_id=context.account_id, region_name=og_region
                ).dynamodb
                table_name = table_name_from_stream_arn(stream_description["StreamArn"])
                stream_name = get_kinesis_stream_name(table_name)
                stream_details = kinesis.describe_stream(StreamName=stream_name)
                table_details = dynamodb.describe_table(TableName=table_name)
                stream_description["KeySchema"] = table_details["Table"]["KeySchema"]
                stream_description["StreamStatus"] = STREAM_STATUS_MAP.get(
                    stream_details["StreamDescription"]["StreamStatus"]
                )

                # Replace Kinesis ShardIDs with ones that mimic actual
                # DynamoDBStream ShardIDs.
                stream_shards = copy.deepcopy(stream_details["StreamDescription"]["Shards"])
                start_index = 0
                for index, shard in enumerate(stream_shards):
                    shard["ShardId"] = get_shard_id(stream, shard["ShardId"])
                    shard.pop("HashKeyRange", None)
                    # we want to ignore the shards before exclusive_start_shard_id parameters
                    # we store the index where we encounter then slice the shards
                    if exclusive_start_shard_id and exclusive_start_shard_id == shard["ShardId"]:
                        start_index = index

                if exclusive_start_shard_id:
                    # slicing the resulting shards after the exclusive_start_shard_id parameters
                    stream_shards = stream_shards[start_index + 1 :]

                stream_description["Shards"] = stream_shards
                stream_description["StreamArn"] = _stream_arn
                return DescribeStreamOutput(StreamDescription=stream_description)

        raise ResourceNotFoundException(
            f"Requested resource not found: Stream: {stream_arn} not found"
        )