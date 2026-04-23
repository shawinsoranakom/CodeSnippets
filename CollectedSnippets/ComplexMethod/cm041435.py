def handler(event, context):
    sqs = create_external_boto_client("sqs")

    print("incoming event:")
    print(json.dumps(event))

    # this lambda expects inputs from an SQS event source mapping
    if not event.get("Records"):
        raise ValueError("no records passed to event")

    batch_item_failures_ids = []

    for record in event["Records"]:
        message = json.loads(record["body"])

        if message.get("fail_attempts") is None:
            raise ValueError("no fail_attempts for the event given")

        if message["fail_attempts"] >= int(record["attributes"]["ApproximateReceiveCount"]):
            batch_item_failures_ids.append(record["messageId"])

    result = {
        "batchItemFailures": [
            {"itemIdentifier": message_id} for message_id in batch_item_failures_ids
        ]
    }

    if os.environ.get("OVERWRITE_RESULT") is not None:
        # try to parse the overwrite result as json
        result = os.environ.get("OVERWRITE_RESULT")
        try:
            result = json.loads(result)
        except Exception:
            pass

    destination_queue_url = os.environ.get("DESTINATION_QUEUE_URL")
    if destination_queue_url:
        sqs.send_message(
            QueueUrl=destination_queue_url,
            MessageBody=json.dumps({"event": event, "result": result}),
        )

    return result