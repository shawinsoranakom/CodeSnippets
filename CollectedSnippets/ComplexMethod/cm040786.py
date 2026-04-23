def publish_batch(
        self,
        context: RequestContext,
        topic_arn: topicARN,
        publish_batch_request_entries: PublishBatchRequestEntryList,
        **kwargs,
    ) -> PublishBatchResponse:
        if len(publish_batch_request_entries) > 10:
            raise TooManyEntriesInBatchRequestException(
                "The batch request contains more entries than permissible."
            )

        parsed_arn = parse_and_validate_topic_arn(topic_arn)
        store = self.get_store(account_id=parsed_arn["account"], region=context.region)
        topic = self._get_topic(topic_arn, context)
        ids = [entry["Id"] for entry in publish_batch_request_entries]
        if len(set(ids)) != len(publish_batch_request_entries):
            raise BatchEntryIdsNotDistinctException(
                "Two or more batch entries in the request have the same Id."
            )

        # Validate each entry ID
        for entry_id in ids:
            if len(entry_id) > 80:
                raise InvalidBatchEntryIdException(
                    f"The Id of a batch entry in the batch request is too long: {entry_id}"
                )
            if not BATCH_ENTRY_ID_REGEX.match(entry_id):
                raise InvalidBatchEntryIdException(
                    f"The Id of a batch entry in the batch request contains an impermissible character: {entry_id}"
                )

        response: PublishBatchResponse = {"Successful": [], "Failed": []}

        # TODO: write AWS validated tests with FilterPolicy and batching
        # TODO: find a scenario where we can fail to send a message synchronously to be able to report it
        # right now, it seems that AWS fails the whole publish if something is wrong in the format of 1 message

        total_batch_size = 0
        message_contexts = []
        for entry_index, entry in enumerate(publish_batch_request_entries, start=1):
            message_payload = entry.get("Message")
            message_attributes = entry.get("MessageAttributes", {})
            if message_attributes:
                # if a message contains non-valid message attributes, it
                # will fail for the first non-valid message encountered, and raise ParameterValueInvalid
                _validate_message_attributes(message_attributes, position=entry_index)

            total_batch_size += _get_total_publish_size(message_payload, message_attributes)

            # TODO: WRITE AWS VALIDATED
            if entry.get("MessageStructure") == "json":
                try:
                    message = json.loads(message_payload)
                    # Keys in the JSON object that correspond to supported transport protocols must have
                    # simple JSON string values.
                    # Non-string values will cause the key to be ignored.
                    message = {
                        key: field for key, field in message.items() if isinstance(field, str)
                    }
                    if "default" not in message:
                        raise InvalidParameterException(
                            "Invalid parameter: Message Structure - No default entry in JSON message body"
                        )
                    entry["Message"] = message  # noqa
                except json.JSONDecodeError:
                    raise InvalidParameterException(
                        "Invalid parameter: Message Structure - JSON message body failed to parse"
                    )

            if is_fifo := (topic_arn.endswith(".fifo")):
                if not all("MessageGroupId" in entry for entry in publish_batch_request_entries):
                    raise InvalidParameterException(
                        "Invalid parameter: The MessageGroupId parameter is required for FIFO topics"
                    )
                if topic["attributes"]["ContentBasedDeduplication"] == "false":
                    if not all(
                        "MessageDeduplicationId" in entry for entry in publish_batch_request_entries
                    ):
                        raise InvalidParameterException(
                            "Invalid parameter: The topic should either have ContentBasedDeduplication enabled or MessageDeduplicationId provided explicitly",
                        )

            msg_ctx = SnsMessage.from_batch_entry(entry, is_fifo=is_fifo)
            message_contexts.append(msg_ctx)
            success = PublishBatchResultEntry(
                Id=entry["Id"],
                MessageId=msg_ctx.message_id,
            )
            if is_fifo:
                success["SequenceNumber"] = msg_ctx.sequencer_number
            response["Successful"].append(success)

        if total_batch_size > MAXIMUM_MESSAGE_LENGTH:
            raise CommonServiceException(
                code="BatchRequestTooLong",
                message="The length of all the messages put together is more than the limit.",
                sender_fault=True,
            )

        publish_ctx = SnsBatchPublishContext(
            messages=message_contexts,
            store=store,
            request_headers=context.request.headers,
            topic_attributes=topic["attributes"],
        )
        self._publisher.publish_batch_to_topic(publish_ctx, topic_arn)

        return response