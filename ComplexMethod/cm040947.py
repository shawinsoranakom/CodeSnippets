def update_kinesis_streaming_destination(
        self,
        context: RequestContext,
        table_name: TableArn,
        stream_arn: StreamArn,
        update_kinesis_streaming_configuration: UpdateKinesisStreamingConfiguration | None = None,
        **kwargs,
    ) -> UpdateKinesisStreamingDestinationOutput:
        self.ensure_table_exists(context.account_id, context.region, table_name)

        if not update_kinesis_streaming_configuration:
            raise ValidationException(
                "Streaming destination cannot be updated with given parameters: "
                "UpdateKinesisStreamingConfiguration cannot be null or contain only null values"
            )

        time_precision = update_kinesis_streaming_configuration.get(
            "ApproximateCreationDateTimePrecision"
        )
        if time_precision not in (
            ApproximateCreationDateTimePrecision.MILLISECOND,
            ApproximateCreationDateTimePrecision.MICROSECOND,
        ):
            raise ValidationException(
                f"1 validation error detected: Value '{time_precision}' at "
                "'updateKinesisStreamingConfiguration.approximateCreationDateTimePrecision' failed to satisfy constraint: "
                "Member must satisfy enum value set: [MILLISECOND, MICROSECOND]"
            )

        store = get_store(context.account_id, context.region)
        table_destinations = store.streaming_destinations.get(table_name) or []

        # filter the right destination based on the stream ARN
        destinations = [d for d in table_destinations if d["StreamArn"] == stream_arn]
        if not destinations:
            raise ValidationException(
                "Table is not in a valid state to enable Kinesis Streaming Destination: "
                f"No streaming destination with streamArn: {stream_arn} found for table with tableName: {table_name}"
            )

        destination = destinations[0]
        table_def = store.table_definitions.get(table_name) or {}
        table_def.setdefault("KinesisDataStreamDestinations", [])

        table_id = store.table_definitions.get(table_name, {}).get("TableId")
        if (
            existing_precision := destination["ApproximateCreationDateTimePrecision"]
        ) == update_kinesis_streaming_configuration["ApproximateCreationDateTimePrecision"]:
            raise ValidationException(
                f"Invalid Request: Precision is already set to the desired value of {existing_precision} "
                f"for tableId: {table_id}, kdsArn: {stream_arn}"
            )
        destination["ApproximateCreationDateTimePrecision"] = time_precision

        return UpdateKinesisStreamingDestinationOutput(
            TableName=table_name,
            StreamArn=stream_arn,
            DestinationStatus=DestinationStatus.UPDATING,
            UpdateKinesisStreamingConfiguration=UpdateKinesisStreamingConfiguration(
                ApproximateCreationDateTimePrecision=time_precision,
            ),
        )