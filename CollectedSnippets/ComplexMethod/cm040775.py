def create_sns_message_body(
    message_context: SnsMessage,
    subscriber: SnsSubscription,
    topic_attributes: dict[str, str] = None,
) -> str:
    message_type = message_context.type or "Notification"
    protocol = subscriber["Protocol"]
    message_content = message_context.message_content(protocol)

    if message_type == "Notification" and is_raw_message_delivery(subscriber):
        return message_content

    external_url = get_cert_base_url()

    data = {
        "Type": message_type,
        "MessageId": message_context.message_id,
        "TopicArn": subscriber["TopicArn"],
        "Message": message_content,
        "Timestamp": timestamp_millis(),
    }

    if message_type == SnsMessageType.Notification:
        unsubscribe_url = create_unsubscribe_url(external_url, subscriber["SubscriptionArn"])
        data["UnsubscribeURL"] = unsubscribe_url

    elif message_type in (
        SnsMessageType.SubscriptionConfirmation,
        SnsMessageType.UnsubscribeConfirmation,
    ):
        data["Token"] = message_context.token
        data["SubscribeURL"] = create_subscribe_url(
            external_url, subscriber["TopicArn"], message_context.token
        )

    if message_context.subject:
        data["Subject"] = message_context.subject

    if message_context.message_attributes:
        data["MessageAttributes"] = prepare_message_attributes(message_context.message_attributes)

    # FIFO topics do not add the signature in the message
    if not subscriber.get("TopicArn", "").endswith(".fifo"):
        signature_version = (
            # we allow for both casings, depending on v1 or v2 provider
            topic_attributes.get("signature_version", topic_attributes.get("SignatureVersion", "1"))
            if topic_attributes
            else "1"
        )
        canonical_string = compute_canonical_string(data, message_type)
        signature = get_message_signature(canonical_string, signature_version=signature_version)
        data.update(
            {
                "SignatureVersion": signature_version,
                "Signature": signature,
                "SigningCertURL": f"{external_url}{sns_constants.SNS_CERT_ENDPOINT}",
            }
        )
    else:
        data["SequenceNumber"] = message_context.sequencer_number

    return json.dumps(data)