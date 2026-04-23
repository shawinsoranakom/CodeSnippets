def store_delivery_log(
    message_context: SnsMessage,
    subscriber: SnsSubscription,
    success: bool,
    topic_attributes: dict[str, str] = None,
    delivery: dict = None,
):
    """
    Store the delivery logs in CloudWatch, configured as TopicAttributes
    See: https://docs.aws.amazon.com/sns/latest/dg/sns-topic-attributes.html#msg-status-sdk

    TODO: for Application, you can also configure Platform attributes:
    See:https://docs.aws.amazon.com/sns/latest/dg/sns-msg-status.html
    """
    # TODO: effectively use `<ENDPOINT>SuccessFeedbackSampleRate` to sample delivery logs
    # TODO: validate format of `delivery` for each Publisher
    # map Protocol to TopicAttribute
    available_delivery_logs_services = {
        "http",
        "https",
        "firehose",
        "lambda",
        "application",
        "sqs",
    }
    # SMS is a special case: https://docs.aws.amazon.com/sns/latest/dg/sms_stats_cloudwatch.html
    # seems like you need to configure on the Console, leave it on by default now in LocalStack
    protocol = subscriber.get("Protocol")
    if protocol != "sms":
        if protocol not in available_delivery_logs_services or not topic_attributes:
            # this service does not have DeliveryLogs feature, return
            return

        # TODO: for now, those attributes are stored as attributes of the moto Topic model in snake case
        # see to work this in our store instead
        role_type = "success" if success else "failure"
        topic_attribute = f"{protocol}_{role_type}_feedback_role_arn"

        # check if topic has the right attribute and a role, otherwise return
        # TODO: on purpose not using walrus operator to show that we get the RoleArn here for CloudWatch
        role_arn = topic_attributes.get(topic_attribute)
        if not role_arn:
            # TODO: remove snake case access once v1 is completely obsolete
            topic_attribute = snake_to_pascal_case(topic_attribute)
            role_arn = topic_attributes.get(topic_attribute)
            if not role_arn:
                return

    if not is_api_enabled("logs"):
        LOG.warning(
            "Service 'logs' is not enabled: skip storing SNS delivery logs. "
            "Please check your 'SERVICES' configuration variable."
        )
        return

    log_group_name = subscriber.get("TopicArn", "")
    for partition in PARTITION_NAMES:
        log_group_name = log_group_name.replace(f"arn:{partition}:", "")
    log_group_name = log_group_name.replace(":", "/")
    log_stream_name = long_uid()
    invocation_time = int(time.time() * 1000)

    delivery = not_none_or(delivery, {})
    delivery["deliveryId"] = long_uid()
    delivery["destination"] = subscriber.get("Endpoint", "")
    delivery["dwellTimeMs"] = 200
    if not success:
        delivery["attemps"] = 1

    if (protocol := subscriber["Protocol"]) == "application":
        protocol = get_platform_type_from_endpoint_arn(subscriber["Endpoint"])

    message = message_context.message_content(protocol)
    delivery_log = {
        "notification": {
            "messageMD5Sum": md5(message),
            "messageId": message_context.message_id,
            "topicArn": subscriber.get("TopicArn"),
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f%z"),
        },
        "delivery": delivery,
        "status": "SUCCESS" if success else "FAILURE",
    }

    log_output = json.dumps(delivery_log)

    # TODO: use the account/region from the role in the TopicAttribute instead, this is what AWS uses
    account_id = extract_account_id_from_arn(subscriber["TopicArn"])
    region_name = extract_region_from_arn(subscriber["TopicArn"])
    logs_client = connect_to(aws_access_key_id=account_id, region_name=region_name).logs

    return store_cloudwatch_logs(
        logs_client, log_group_name, log_stream_name, log_output, invocation_time
    )