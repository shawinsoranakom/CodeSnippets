def handler(event, context):
    """Generic event forwarder Lambda."""

    # print test messages (to test CloudWatch Logs integration)
    print("Lambda log message - print function", flush=True)
    LOGGER.info("Lambda log message - logging module")
    LOGGER.flush()

    if MSG_BODY_RAISE_ERROR_FLAG in event:
        raise Exception("Test exception (this is intentional)")

    if "httpMethod" in event:
        # looks like this is a call from an AWS_PROXY API Gateway
        try:
            body = json.loads(event["body"])
        except Exception:
            body = {}

        body["path"] = event.get("path")
        body["resource"] = event.get("resource")
        body["pathParameters"] = event.get("pathParameters")
        body["requestContext"] = event.get("requestContext")
        body["queryStringParameters"] = event.get("queryStringParameters")
        body["httpMethod"] = event.get("httpMethod")
        body["body"] = event.get("body")
        body["headers"] = event.get("headers")
        body["isBase64Encoded"] = event.get("isBase64Encoded")
        if body["httpMethod"] == "DELETE":
            return {"statusCode": 204, "body": ""}

        # This parameter is often just completely excluded from the response.
        base64_response = {}
        is_base_64_encoded = body.get("return_is_base_64_encoded")
        if is_base_64_encoded is not None:
            base64_response["isBase64Encoded"] = is_base_64_encoded

        status_code = body.get("return_status_code", 200)
        headers = body.get("return_headers", {})
        body = body.get("return_raw_body") or body

        return {
            "body": body,
            "statusCode": status_code,
            "isBase64Encoded": is_base_64_encoded,
            "headers": headers,
            "multiValueHeaders": {"set-cookie": ["language=en-US", "theme=blue moon"]},
            **base64_response,
        }
    if MSG_BODY_DELETE_BATCH in event:
        sqs_client = create_external_boto_client("sqs")
        queue_url = event.get(MSG_BODY_DELETE_BATCH)
        message = sqs_client.receive_message(QueueUrl=queue_url)["Messages"][0]
        sqs_client.delete_message(QueueUrl=queue_url, ReceiptHandle=message["ReceiptHandle"])
        messages = sqs_client.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=10)[
            "Messages"
        ]
        entries = [message["ReceiptHandle"] for message in messages]
        sqs_client.delete_message_batch(QueueUrl=queue_url, Entries=entries)

    if "Records" not in event:
        result_map = {"event": event, "context": {}}
        result_map["context"]["invoked_function_arn"] = context.invoked_function_arn
        result_map["context"]["function_version"] = context.function_version
        result_map["context"]["function_name"] = context.function_name
        result_map["context"]["memory_limit_in_mb"] = context.memory_limit_in_mb
        result_map["context"]["aws_request_id"] = context.aws_request_id
        result_map["context"]["log_group_name"] = context.log_group_name
        result_map["context"]["log_stream_name"] = context.log_stream_name

        if hasattr(context, "client_context"):
            result_map["context"]["client_context"] = context.client_context

        return result_map

    raw_event_messages = []
    for record in event["Records"]:
        # Deserialize into Python dictionary and extract the
        # "NewImage" (the new version of the full ddb document)
        ddb_new_image = deserialize_event(record)

        if MSG_BODY_RAISE_ERROR_FLAG in ddb_new_image.get("data", {}):
            raise Exception("Test exception (this is intentional)")

        # Place the raw event message document into the Kinesis message format
        kinesis_record = {"PartitionKey": "key123", "Data": json.dumps(ddb_new_image)}

        if MSG_BODY_MESSAGE_TARGET in ddb_new_image.get("data", {}):
            forwarding_target = ddb_new_image["data"][MSG_BODY_MESSAGE_TARGET]
            target_name = forwarding_target.split(":")[-1]
            if forwarding_target.startswith("kinesis:"):
                ddb_new_image["data"][MSG_BODY_MESSAGE_TARGET] = "s3:test_chain_result"
                kinesis_record["Data"] = json.dumps(ddb_new_image["data"])
                forward_event_to_target_stream(kinesis_record, target_name)
            elif forwarding_target.startswith("s3:"):
                s3_client = create_external_boto_client("s3")
                test_data = to_bytes(json.dumps({"test_data": ddb_new_image["data"]["test_data"]}))
                s3_client.upload_fileobj(BytesIO(test_data), TEST_BUCKET_NAME, target_name)
        else:
            raw_event_messages.append(kinesis_record)

    # Forward messages to Kinesis
    forward_events(raw_event_messages)