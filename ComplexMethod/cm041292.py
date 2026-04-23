def _send_to_dead_letter_queue(source_arn: str, dlq_arn: str, event: dict, error, role: str = None):
    if not dlq_arn:
        return
    LOG.info("Sending failed execution %s to dead letter queue %s", source_arn, dlq_arn)
    messages = _prepare_messages_to_dlq(source_arn, event, error)
    source_service = arns.extract_service_from_arn(source_arn)
    region = arns.extract_region_from_arn(dlq_arn)
    if role:
        clients = connect_to.with_assumed_role(
            role_arn=role, service_principal=source_service, region_name=region
        )
    else:
        clients = connect_to(region_name=region)
    if ":sqs:" in dlq_arn:
        queue_url = arns.sqs_queue_url_for_arn(dlq_arn)
        sqs_client = clients.sqs.request_metadata(
            source_arn=source_arn, service_principal=source_service
        )
        error = None
        result_code = None
        try:
            result = sqs_client.send_message_batch(QueueUrl=queue_url, Entries=messages)
            result_code = result.get("ResponseMetadata", {}).get("HTTPStatusCode")
        except Exception as e:
            error = e
        if error or not result_code or result_code >= 400:
            msg = f"Unable to send message to dead letter queue {queue_url} (code {result_code}): {error}"
            if "InvalidMessageContents" in str(error):
                msg += f" - messages: {messages}"
            LOG.info(msg)
            raise Exception(msg)
    elif ":sns:" in dlq_arn:
        sns_client = clients.sns.request_metadata(
            source_arn=source_arn, service_principal=source_service
        )
        for message in messages:
            sns_client.publish(
                TopicArn=dlq_arn,
                Message=message["MessageBody"],
                MessageAttributes=message["MessageAttributes"],
            )
    else:
        LOG.warning("Unsupported dead letter queue type: %s", dlq_arn)
    return dlq_arn