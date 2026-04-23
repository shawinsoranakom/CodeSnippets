def validate_subscription_attribute(
    attribute_name: str,
    attribute_value: str,
    topic_arn: str,
    endpoint: str,
    is_subscribe_call: bool = False,
) -> None:
    """
    Validate the subscription attribute to be set. See:
    https://docs.aws.amazon.com/sns/latest/api/API_SetSubscriptionAttributes.html
    :param attribute_name: the subscription attribute name, must be in VALID_SUBSCRIPTION_ATTR_NAME
    :param attribute_value: the subscription attribute value
    :param topic_arn: the topic_arn of the subscription, needed to know if it is FIFO
    :param endpoint: the subscription endpoint (like an SQS queue ARN)
    :param is_subscribe_call: the error message is different if called from Subscribe or SetSubscriptionAttributes
    :raises InvalidParameterException
    :return:
    """
    error_prefix = (
        "Invalid parameter: Attributes Reason: " if is_subscribe_call else "Invalid parameter: "
    )
    if attribute_name not in VALID_SUBSCRIPTION_ATTR_NAME:
        raise InvalidParameterException(f"{error_prefix}AttributeName")

    if attribute_name == "FilterPolicy":
        try:
            json.loads(attribute_value or "{}")
        except json.JSONDecodeError:
            raise InvalidParameterException(f"{error_prefix}FilterPolicy: failed to parse JSON.")
    elif attribute_name == "FilterPolicyScope":
        if attribute_value not in ("MessageAttributes", "MessageBody"):
            raise InvalidParameterException(
                f"{error_prefix}FilterPolicyScope: Invalid value [{attribute_value}]. "
                f"Please use either MessageBody or MessageAttributes"
            )
    elif attribute_name == "RawMessageDelivery":
        # TODO: only for SQS and https(s) subs, + firehose
        if attribute_value.lower() not in ("true", "false"):
            raise InvalidParameterException(
                f"{error_prefix}RawMessageDelivery: Invalid value [{attribute_value}]. "
                f"Must be true or false."
            )

    elif attribute_name == "RedrivePolicy":
        try:
            dlq_target_arn = json.loads(attribute_value).get("deadLetterTargetArn", "")
        except json.JSONDecodeError:
            raise InvalidParameterException(f"{error_prefix}RedrivePolicy: failed to parse JSON.")
        try:
            parsed_arn = parse_arn(dlq_target_arn)
        except InvalidArnException:
            raise InvalidParameterException(
                f"{error_prefix}RedrivePolicy: deadLetterTargetArn is an invalid arn"
            )

        if topic_arn.endswith(".fifo"):
            if endpoint.endswith(".fifo") and (
                not parsed_arn["resource"].endswith(".fifo") or "sqs" not in parsed_arn["service"]
            ):
                raise InvalidParameterException(
                    f"{error_prefix}RedrivePolicy: must use a FIFO queue as DLQ for a FIFO Subscription to a FIFO Topic."
                )