def receive_message(
        self,
        context: RequestContext,
        queue_url: String,
        attribute_names: AttributeNameList = None,
        message_system_attribute_names: MessageSystemAttributeList = None,
        message_attribute_names: MessageAttributeNameList = None,
        max_number_of_messages: NullableInteger = None,
        visibility_timeout: NullableInteger = None,
        wait_time_seconds: NullableInteger = None,
        receive_request_attempt_id: String = None,
        **kwargs,
    ) -> ReceiveMessageResult:
        # TODO add support for message_system_attribute_names
        queue = self._resolve_queue(context, queue_url=queue_url)

        poll_empty_queue = False
        if override := extract_wait_time_seconds_from_headers(context):
            wait_time_seconds = override
            poll_empty_queue = True
        elif wait_time_seconds is None:
            wait_time_seconds = queue.wait_time_seconds
        elif wait_time_seconds < 0 or wait_time_seconds > 20:
            raise InvalidParameterValueException(
                f"Value {wait_time_seconds} for parameter WaitTimeSeconds is invalid. "
                f"Reason: Must be >= 0 and <= 20, if provided."
            )
        num = max_number_of_messages or 1

        # override receive count with value from custom header
        if override := extract_message_count_from_headers(context):
            num = override
        elif num == -1:
            # backdoor to get all messages
            num = queue.approximate_number_of_messages
        elif (
            num < 1 or num > MAX_NUMBER_OF_MESSAGES
        ) and not SQS_DISABLE_MAX_NUMBER_OF_MESSAGE_LIMIT:
            raise InvalidParameterValueException(
                f"Value {num} for parameter MaxNumberOfMessages is invalid. "
                f"Reason: Must be between 1 and 10, if provided."
            )

        # we chose to always return the maximum possible number of messages, even though AWS will typically return
        # fewer messages than requested on small queues. at some point we could maybe change this to randomly sample
        # between 1 and max_number_of_messages.
        # see https://docs.aws.amazon.com/AWSSimpleQueueService/latest/APIReference/API_ReceiveMessage.html
        result = queue.receive(
            num, wait_time_seconds, visibility_timeout, poll_empty_queue=poll_empty_queue
        )

        # process dead letter messages
        if result.dead_letter_messages:
            dead_letter_target_arn = queue.redrive_policy["deadLetterTargetArn"]
            dl_queue = self._require_queue_by_arn(context, dead_letter_target_arn)
            # TODO: does this need to be atomic?
            for standard_message in result.dead_letter_messages:
                message = standard_message.message
                message["Attributes"][MessageSystemAttributeName.DeadLetterQueueSourceArn] = (
                    queue.arn
                )
                dl_queue.put(
                    message=message,
                    message_deduplication_id=standard_message.message_deduplication_id,
                    message_group_id=standard_message.message_group_id,
                )

                if isinstance(queue, FifoQueue):
                    message_group = queue.get_message_group(standard_message.message_group_id)
                    queue.update_message_group_visibility(message_group)

        # prepare result
        messages = []
        message_system_attribute_names = message_system_attribute_names or attribute_names
        for i, standard_message in enumerate(result.successful):
            message = to_sqs_api_message(
                standard_message, message_system_attribute_names, message_attribute_names
            )
            message["ReceiptHandle"] = result.receipt_handles[i]
            messages.append(message)

        if self._cloudwatch_dispatcher:
            self._cloudwatch_dispatcher.dispatch_metric_received(queue, received=len(messages))

        # TODO: how does receiving behave if the queue was deleted in the meantime?
        return ReceiveMessageResult(Messages=(messages if messages else None))