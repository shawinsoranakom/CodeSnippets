def enable_kinesis_streaming_destination(
        self,
        context: RequestContext,
        table_name: TableName,
        stream_arn: StreamArn,
        enable_kinesis_streaming_configuration: EnableKinesisStreamingConfiguration = None,
        **kwargs,
    ) -> KinesisStreamingDestinationOutput:
        self.ensure_table_exists(
            context.account_id,
            context.region,
            table_name,
            error_message=f"Requested resource not found: Table: {table_name} not found",
        )

        # TODO: Use the time precision in config if set
        enable_kinesis_streaming_configuration = enable_kinesis_streaming_configuration or {}

        stream = self._event_forwarder.is_kinesis_stream_exists(stream_arn=stream_arn)
        if not stream:
            raise ValidationException("User does not have a permission to use kinesis stream")

        store = get_store(context.account_id, context.region)
        streaming_destinations = store.streaming_destinations.get(table_name) or []

        destinations = [d for d in streaming_destinations if d["StreamArn"] == stream_arn]
        if destinations:
            status = destinations[0].get("DestinationStatus", None)
            if status not in ["DISABLED", "ENABLED_FAILED", None]:
                raise ValidationException(
                    "Table is not in a valid state to enable Kinesis Streaming "
                    "Destination:EnableKinesisStreamingDestination must be DISABLED or ENABLE_FAILED "
                    "to perform ENABLE operation."
                )

        # remove the stream destination if already present
        store.streaming_destinations[table_name] = [
            _d for _d in streaming_destinations if _d["StreamArn"] != stream_arn
        ]
        # append the active stream destination at the end of the list
        store.streaming_destinations[table_name].append(
            KinesisDataStreamDestination(
                DestinationStatus=DestinationStatus.ACTIVE,
                DestinationStatusDescription="Stream is active",
                StreamArn=stream_arn,
                ApproximateCreationDateTimePrecision=ApproximateCreationDateTimePrecision.MILLISECOND,
            )
        )
        return KinesisStreamingDestinationOutput(
            DestinationStatus=DestinationStatus.ENABLING,
            StreamArn=stream_arn,
            TableName=table_name,
            EnableKinesisStreamingConfiguration=enable_kinesis_streaming_configuration,
        )