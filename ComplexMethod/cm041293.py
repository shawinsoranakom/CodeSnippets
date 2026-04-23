def _prepare_messages_to_dlq(source_arn: str, event: dict, error) -> list[dict]:
    messages = []
    custom_attrs = {
        "RequestID": {"DataType": "String", "StringValue": str(uuid.uuid4())},
        "ErrorCode": {"DataType": "String", "StringValue": "200"},
        "ErrorMessage": {"DataType": "String", "StringValue": str(error)},
    }
    if ":sqs:" in source_arn:
        custom_attrs["ErrorMessage"]["StringValue"] = str(error.result)
        for record in event.get("Records", []):
            msg_attrs = message_attributes_to_upper(record.get("messageAttributes"))
            message_attrs = {**msg_attrs, **custom_attrs}
            messages.append(
                {
                    "Id": record.get("messageId"),
                    "MessageBody": record.get("body"),
                    "MessageAttributes": message_attrs,
                }
            )
    elif ":sns:" in source_arn:
        # event can also contain: MessageAttributes, MessageGroupId, MessageDeduplicationId
        message = {
            "Id": str(uuid.uuid4()),
            "MessageBody": event.pop("message"),
            **event,
        }
        messages.append(message)

    elif ":lambda:" in source_arn:
        custom_attrs["ErrorCode"]["DataType"] = "Number"
        # not sure about what type of error can come here
        try:
            error_message = json.loads(error.result)["errorMessage"]
            custom_attrs["ErrorMessage"]["StringValue"] = error_message
        except (ValueError, KeyError):
            # using old behaviour
            custom_attrs["ErrorMessage"]["StringValue"] = str(error)

        messages.append(
            {
                "Id": str(uuid.uuid4()),
                "MessageBody": json.dumps(event),
                "MessageAttributes": custom_attrs,
            }
        )
    # make sure we only have printable strings in the message attributes
    for message in messages:
        if message.get("MessageAttributes"):
            message["MessageAttributes"] = convert_to_printable_chars(message["MessageAttributes"])
    return messages