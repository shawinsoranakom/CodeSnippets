def subscribe(
        self,
        context: RequestContext,
        topic_arn: topicARN,
        protocol: protocol,
        endpoint: endpoint | None = None,
        attributes: SubscriptionAttributesMap | None = None,
        return_subscription_arn: bool | None = None,
        **kwargs,
    ) -> SubscribeResponse:
        parsed_topic_arn = parse_and_validate_topic_arn(topic_arn)
        if context.region != parsed_topic_arn["region"]:
            raise InvalidParameterException("Invalid parameter: TopicArn")

        store = self.get_store(account_id=parsed_topic_arn["account"], region=context.region)

        topic = self._get_topic(arn=topic_arn, context=context)
        topic_subscriptions = topic["subscriptions"]
        if not endpoint:
            # TODO: check AWS behaviour (because endpoint is optional)
            raise NotFoundException("Endpoint not specified in subscription")
        if protocol not in SNS_PROTOCOLS:
            raise InvalidParameterException(
                f"Invalid parameter: Amazon SNS does not support this protocol string: {protocol}"
            )
        elif protocol in ["http", "https"] and not endpoint.startswith(f"{protocol}://"):
            raise InvalidParameterException(
                "Invalid parameter: Endpoint must match the specified protocol"
            )
        elif protocol == "sms" and not is_valid_e164_number(endpoint):
            raise InvalidParameterException(f"Invalid SMS endpoint: {endpoint}")

        elif protocol == "sqs":
            try:
                parse_arn(endpoint)
            except InvalidArnException:
                raise InvalidParameterException("Invalid parameter: SQS endpoint ARN")

        elif protocol == "application":
            # TODO: Validate exact behaviour
            try:
                parse_arn(endpoint)
            except InvalidArnException:
                raise InvalidParameterException("Invalid parameter: ApplicationEndpoint ARN")

        if ".fifo" in endpoint and ".fifo" not in topic_arn:
            # TODO: move to sqs protocol block if possible
            raise InvalidParameterException(
                "Invalid parameter: Invalid parameter: Endpoint Reason: FIFO SQS Queues can not be subscribed to standard SNS topics"
            )

        sub_attributes = copy.deepcopy(attributes) if attributes else None
        if sub_attributes:
            for attr_name, attr_value in sub_attributes.items():
                validate_subscription_attribute(
                    attribute_name=attr_name,
                    attribute_value=attr_value,
                    topic_arn=topic_arn,
                    endpoint=endpoint,
                    is_subscribe_call=True,
                )
                if raw_msg_delivery := sub_attributes.get("RawMessageDelivery"):
                    sub_attributes["RawMessageDelivery"] = raw_msg_delivery.lower()

        # An endpoint may only be subscribed to a topic once. Subsequent
        # subscribe calls do nothing (subscribe is idempotent), except if its attributes are different.
        for existing_topic_subscription in topic_subscriptions:
            sub = store.subscriptions.get(existing_topic_subscription, {})
            if sub.get("Endpoint") == endpoint:
                if sub_attributes:
                    # validate the subscription attributes aren't different
                    for attr in VALID_SUBSCRIPTION_ATTR_NAME:
                        # if a new attribute is present and different from an existent one, raise
                        if (new_attr := sub_attributes.get(attr)) and sub.get(attr) != new_attr:
                            raise InvalidParameterException(
                                "Invalid parameter: Attributes Reason: Subscription already exists with different attributes"
                            )

                return SubscribeResponse(SubscriptionArn=sub["SubscriptionArn"])
        principal = DUMMY_SUBSCRIPTION_PRINCIPAL.format(
            partition=get_partition(context.region), account_id=context.account_id
        )
        subscription_arn = create_subscription_arn(topic_arn)
        subscription = SnsSubscription(
            # http://docs.aws.amazon.com/cli/latest/reference/sns/get-subscription-attributes.html
            TopicArn=topic_arn,
            Endpoint=endpoint,
            Protocol=protocol,
            SubscriptionArn=subscription_arn,
            PendingConfirmation="true",
            Owner=context.account_id,
            RawMessageDelivery="false",  # default value, will be overridden if set
            FilterPolicyScope="MessageAttributes",  # default value, will be overridden if set
            SubscriptionPrincipal=principal,  # dummy value, could be fetched with a call to STS?
        )
        if sub_attributes:
            subscription.update(sub_attributes)
            if "FilterPolicy" in sub_attributes:
                filter_policy = (
                    json.loads(sub_attributes["FilterPolicy"])
                    if sub_attributes["FilterPolicy"]
                    else None
                )
                if filter_policy:
                    validator = FilterPolicyValidator(
                        scope=subscription.get("FilterPolicyScope", "MessageAttributes"),
                        is_subscribe_call=True,
                    )
                    validator.validate_filter_policy(filter_policy)

                store.subscription_filter_policy[subscription_arn] = filter_policy

        store.subscriptions[subscription_arn] = subscription

        topic_subscriptions.append(subscription_arn)

        # store the token and subscription arn
        # TODO: the token is a 288 hex char string
        subscription_token = encode_subscription_token_with_region(region=context.region)
        store.subscription_tokens[subscription_token] = subscription_arn

        response_subscription_arn = subscription_arn
        # Send out confirmation message for HTTP(S), fix for https://github.com/localstack/localstack/issues/881
        if protocol in ["http", "https"]:
            message_ctx = SnsMessage(
                type=SnsMessageType.SubscriptionConfirmation,
                token=subscription_token,
                message=f"You have chosen to subscribe to the topic {topic_arn}.\nTo confirm the subscription, visit the SubscribeURL included in this message.",
            )
            publish_ctx = SnsPublishContext(
                message=message_ctx,
                store=store,
                request_headers=context.request.headers,
                topic_attributes=topic["attributes"],
            )
            self._publisher.publish_to_topic_subscriber(
                ctx=publish_ctx,
                topic_arn=topic_arn,
                subscription_arn=subscription_arn,
            )
            if not return_subscription_arn:
                response_subscription_arn = "pending confirmation"

        elif protocol not in ["email", "email-json"]:
            # Only HTTP(S) and email subscriptions are not auto validated
            # Except if the endpoint and the topic are not in the same AWS account, then you'd need to manually confirm
            # the subscription with the token
            # TODO: revisit for multi-account
            # TODO: test with AWS for email & email-json confirmation message
            # we need to add the following check:
            # if parsed_topic_arn["account"] == endpoint account (depending on the type, SQS, lambda, parse the arn)
            subscription["PendingConfirmation"] = "false"
            subscription["ConfirmationWasAuthenticated"] = "true"

        return SubscribeResponse(SubscriptionArn=response_subscription_arn)