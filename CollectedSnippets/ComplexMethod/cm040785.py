def publish(
        self,
        context: RequestContext,
        message: message,
        topic_arn: topicARN | None = None,
        target_arn: String | None = None,
        phone_number: PhoneNumber | None = None,
        subject: subject | None = None,
        message_structure: messageStructure | None = None,
        message_attributes: MessageAttributeMap | None = None,
        message_deduplication_id: String | None = None,
        message_group_id: String | None = None,
        **kwargs,
    ) -> PublishResponse:
        if subject == "":
            raise InvalidParameterException("Invalid parameter: Subject")
        if not message or all(not m for m in message):
            raise InvalidParameterException("Invalid parameter: Empty message")

        # TODO: check for topic + target + phone number at the same time?
        # TODO: more validation on phone, it might be opted out?
        if phone_number and not is_valid_e164_number(phone_number):
            raise InvalidParameterException(
                f"Invalid parameter: PhoneNumber Reason: {phone_number} is not valid to publish to"
            )

        if message_attributes:
            _validate_message_attributes(message_attributes)

        if _get_total_publish_size(message, message_attributes) > MAXIMUM_MESSAGE_LENGTH:
            raise InvalidParameterException("Invalid parameter: Message too long")

        # for compatibility reasons, AWS allows users to use either TargetArn or TopicArn for publishing to a topic
        # use any of them for topic validation
        topic_or_target_arn = topic_arn or target_arn
        topic = None

        if is_fifo := (topic_or_target_arn and ".fifo" in topic_or_target_arn):
            if not message_group_id:
                raise InvalidParameterException(
                    "Invalid parameter: The MessageGroupId parameter is required for FIFO topics",
                )
            topic = self._get_topic(topic_or_target_arn, context)
            if topic["attributes"]["ContentBasedDeduplication"] == "false":
                if not message_deduplication_id:
                    raise InvalidParameterException(
                        "Invalid parameter: The topic should either have ContentBasedDeduplication enabled or MessageDeduplicationId provided explicitly",
                    )
        elif message_deduplication_id:
            # this is the first one to raise if both are set while the topic is not fifo
            raise InvalidParameterException(
                "Invalid parameter: MessageDeduplicationId Reason: The request includes MessageDeduplicationId parameter that is not valid for this topic type"
            )

        is_endpoint_publish = target_arn and ":endpoint/" in target_arn
        if message_structure == "json":
            try:
                message = json.loads(message)
                # Keys in the JSON object that correspond to supported transport protocols must have
                # simple JSON string values.
                # Non-string values will cause the key to be ignored.
                message = {key: field for key, field in message.items() if isinstance(field, str)}
                # TODO: check no default key for direct TargetArn endpoint publish, need credentials
                # see example: https://docs.aws.amazon.com/sns/latest/dg/sns-send-custom-platform-specific-payloads-mobile-devices.html
                if "default" not in message and not is_endpoint_publish:
                    raise InvalidParameterException(
                        "Invalid parameter: Message Structure - No default entry in JSON message body"
                    )
            except json.JSONDecodeError:
                raise InvalidParameterException(
                    "Invalid parameter: Message Structure - JSON message body failed to parse"
                )

        if not phone_number:
            # use the account to get the store from the TopicArn (you can only publish in the same region as the topic)
            parsed_arn = parse_and_validate_topic_arn(topic_or_target_arn)
            store = self.get_store(account_id=parsed_arn["account"], region=context.region)
            if is_endpoint_publish:
                if not (platform_endpoint := store.platform_endpoints.get(target_arn)):
                    raise InvalidParameterException(
                        "Invalid parameter: TargetArn Reason: No endpoint found for the target arn specified"
                    )
                elif (
                    not platform_endpoint.platform_endpoint["Attributes"]
                    .get("Enabled", "false")
                    .lower()
                    == "true"
                ):
                    raise EndpointDisabledException("Endpoint is disabled")
            else:
                topic = self._get_topic(topic_or_target_arn, context)
        else:
            # use the store from the request context
            store = self.get_store(account_id=context.account_id, region=context.region)

        message_ctx = SnsMessage(
            type=SnsMessageType.Notification,
            message=message,
            message_attributes=message_attributes,
            message_deduplication_id=message_deduplication_id,
            message_group_id=message_group_id,
            message_structure=message_structure,
            subject=subject,
            is_fifo=is_fifo,
        )
        publish_ctx = SnsPublishContext(
            message=message_ctx, store=store, request_headers=context.request.headers
        )

        if is_endpoint_publish:
            self._publisher.publish_to_application_endpoint(
                ctx=publish_ctx, endpoint_arn=target_arn
            )
        elif phone_number:
            self._publisher.publish_to_phone_number(ctx=publish_ctx, phone_number=phone_number)
        else:
            # beware if the subscription is FIFO, the order might not be guaranteed.
            # 2 quick call to this method in succession might not be executed in order in the executor?
            # TODO: test how this behaves in a FIFO context with a lot of threads.
            publish_ctx.topic_attributes |= topic["attributes"]
            self._publisher.publish_to_topic(publish_ctx, topic_or_target_arn)

        if is_fifo:
            return PublishResponse(
                MessageId=message_ctx.message_id, SequenceNumber=message_ctx.sequencer_number
            )

        return PublishResponse(MessageId=message_ctx.message_id)