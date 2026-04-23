def moto_put_log_events(self: "MotoLogStream", log_events):
    # TODO: call/patch upstream method here, instead of duplicating the code!
    self.last_ingestion_time = int(unix_time_millis())
    self.stored_bytes += sum([len(log_event["message"]) for log_event in log_events])
    events = [LogEvent(self.last_ingestion_time, log_event) for log_event in log_events]
    self.events += events
    self.upload_sequence_token += 1

    # apply filter_pattern -> only forward what matches the pattern
    for subscription_filter in self.log_group.subscription_filters.values():
        if subscription_filter.filter_pattern:
            # TODO only patched in pro
            matches = get_pattern_matcher(subscription_filter.filter_pattern)
            events = [
                LogEvent(self.last_ingestion_time, event)
                for event in log_events
                if matches(subscription_filter.filter_pattern, event)
            ]

        if events and subscription_filter.destination_arn:
            destination_arn = subscription_filter.destination_arn
            log_events = [
                {
                    "id": str(event.event_id),
                    "timestamp": event.timestamp,
                    "message": event.message,
                }
                for event in events
            ]

            data = {
                "messageType": "DATA_MESSAGE",
                "owner": self.account_id,  # AWS Account ID of the originating log data
                "logGroup": self.log_group.name,
                "logStream": self.log_stream_name,
                "subscriptionFilters": [subscription_filter.name],
                "logEvents": log_events,
            }

            output = io.BytesIO()
            with GzipFile(fileobj=output, mode="w") as f:
                f.write(json.dumps(data, separators=(",", ":")).encode("utf-8"))
            payload_gz_encoded = output.getvalue()
            event = {"awslogs": {"data": base64.b64encode(output.getvalue()).decode("utf-8")}}

            log_group_arn = arns.log_group_arn(self.log_group.name, self.account_id, self.region)
            arn_data = arns.parse_arn(destination_arn)

            if subscription_filter.role_arn:
                factory = connect_to.with_assumed_role(
                    role_arn=subscription_filter.role_arn,
                    service_principal=ServicePrincipal.logs,
                    region_name=arn_data["region"],
                )
            else:
                factory = connect_to(
                    aws_access_key_id=arn_data["account"], region_name=arn_data["region"]
                )

            if ":lambda:" in destination_arn:
                client = factory.lambda_.request_metadata(
                    source_arn=log_group_arn, service_principal=ServicePrincipal.logs
                )
                client.invoke(FunctionName=destination_arn, Payload=json.dumps(event))

            if ":kinesis:" in destination_arn:
                client = factory.kinesis.request_metadata(
                    source_arn=log_group_arn, service_principal=ServicePrincipal.logs
                )
                stream_name = arns.kinesis_stream_name(destination_arn)
                client.put_record(
                    StreamName=stream_name,
                    Data=payload_gz_encoded,
                    PartitionKey=self.log_group.name,
                )

            if ":firehose:" in destination_arn:
                client = factory.firehose.request_metadata(
                    source_arn=log_group_arn, service_principal=ServicePrincipal.logs
                )
                firehose_name = arns.firehose_name(destination_arn)
                client.put_record(
                    DeliveryStreamName=firehose_name,
                    Record={"Data": payload_gz_encoded},
                )

    return f"{self.upload_sequence_token:056d}"