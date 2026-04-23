def send_event_to_target(
    target_arn: str,
    event: dict,
    target_attributes: dict = None,
    asynchronous: bool = True,
    target: dict = None,
    role: str = None,
    source_arn: str = None,
    source_service: str = None,
    events_source: str = None,  # optional data for publishing to EventBridge
    events_detail_type: str = None,  # optional data for publishing to EventBridge
):
    region = extract_region_from_arn(target_arn)
    account_id = extract_account_id_from_arn(source_arn)

    if target is None:
        target = {}
    if role:
        clients = connect_to.with_assumed_role(
            role_arn=role, service_principal=source_service, region_name=region
        )
    else:
        clients = connect_to(aws_access_key_id=account_id, region_name=region)

    if ":lambda:" in target_arn:
        lambda_client = clients.lambda_.request_metadata(
            service_principal=source_service, source_arn=source_arn
        )
        lambda_client.invoke(
            FunctionName=target_arn,
            Payload=to_bytes(json.dumps(event)),
            InvocationType="Event" if asynchronous else "RequestResponse",
        )

    elif ":sns:" in target_arn:
        sns_client = clients.sns.request_metadata(
            service_principal=source_service, source_arn=source_arn
        )
        sns_client.publish(TopicArn=target_arn, Message=json.dumps(event))

    elif ":sqs:" in target_arn:
        sqs_client = clients.sqs.request_metadata(
            service_principal=source_service, source_arn=source_arn
        )
        queue_url = sqs_queue_url_for_arn(target_arn)
        msg_group_id = collections.get_safe(target_attributes, "$.SqsParameters.MessageGroupId")
        kwargs = {"MessageGroupId": msg_group_id} if msg_group_id else {}
        sqs_client.send_message(
            QueueUrl=queue_url, MessageBody=json.dumps(event, separators=(",", ":")), **kwargs
        )

    elif ":states:" in target_arn:
        account_id = extract_account_id_from_arn(target_arn)
        stepfunctions_client = connect_to(
            aws_access_key_id=account_id, region_name=region
        ).stepfunctions
        stepfunctions_client.start_execution(stateMachineArn=target_arn, input=json.dumps(event))

    elif ":firehose:" in target_arn:
        delivery_stream_name = firehose_name(target_arn)
        firehose_client = clients.firehose.request_metadata(
            service_principal=source_service, source_arn=source_arn
        )
        firehose_client.put_record(
            DeliveryStreamName=delivery_stream_name,
            Record={"Data": to_bytes(json.dumps(event))},
        )

    elif ":events:" in target_arn:
        if ":api-destination/" in target_arn or ":destination/" in target_arn:
            send_event_to_api_destination(target_arn, event, target.get("HttpParameters"))

        else:
            events_client = clients.events.request_metadata(
                service_principal=source_service, source_arn=source_arn
            )
            eventbus_name = target_arn.split(":")[-1].split("/")[-1]
            detail = event.get("detail") or event
            resources = event.get("resources") or [source_arn] if source_arn else []
            events_client.put_events(
                Entries=[
                    {
                        "EventBusName": eventbus_name,
                        "Source": events_source or event.get("source", source_service) or "",
                        "DetailType": events_detail_type or event.get("detail-type", ""),
                        "Detail": json.dumps(detail),
                        "Resources": resources,
                    }
                ]
            )

    elif ":kinesis:" in target_arn:
        partition_key_path = collections.get_safe(
            target_attributes,
            "$.KinesisParameters.PartitionKeyPath",
            default_value="$.id",
        )

        stream_name = target_arn.split("/")[-1]
        partition_key = collections.get_safe(event, partition_key_path, event["id"])
        kinesis_client = clients.kinesis.request_metadata(
            service_principal=source_service, source_arn=source_arn
        )

        kinesis_client.put_record(
            StreamName=stream_name,
            Data=to_bytes(json.dumps(event)),
            PartitionKey=partition_key,
        )

    elif ":logs:" in target_arn:
        log_group_name = target_arn.split(":")[6]
        logs_client = clients.logs.request_metadata(
            service_principal=source_service, source_arn=source_arn
        )
        log_stream_name = str(uuid.uuid4())
        logs_client.create_log_stream(logGroupName=log_group_name, logStreamName=log_stream_name)
        logs_client.put_log_events(
            logGroupName=log_group_name,
            logStreamName=log_stream_name,
            logEvents=[{"timestamp": now_utc(millis=True), "message": json.dumps(event)}],
        )
    else:
        LOG.warning('Unsupported Events rule target ARN: "%s"', target_arn)