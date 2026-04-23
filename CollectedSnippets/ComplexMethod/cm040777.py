def get_sqs_kwargs(msg_context: SnsMessage, subscriber: SnsSubscription):
        kwargs = {}
        if is_raw_message_delivery(subscriber) and msg_context.message_attributes:
            kwargs["MessageAttributes"] = msg_context.message_attributes

        # SNS now allows regular non-fifo subscriptions to FIFO topics. Validate that the subscription target is fifo
        # before passing the FIFO-only parameters

        # SNS will only forward the `MessageGroupId` for Fair Queues in some scenarios:
        # - non-FIFO SNS topic to Fair Queue
        # - FIFO topic to FIFO queue
        # It will NOT forward it with FIFO topic to regular Queue (possibly used for internal grouping without relying
        # on SQS capabilities)
        if subscriber["TopicArn"].endswith(".fifo"):
            if subscriber["Endpoint"].endswith(".fifo"):
                if msg_context.message_group_id:
                    kwargs["MessageGroupId"] = msg_context.message_group_id
                if msg_context.message_deduplication_id:
                    kwargs["MessageDeduplicationId"] = msg_context.message_deduplication_id
                else:
                    # SNS uses the message body provided to generate a unique hash value to use as the deduplication ID
                    # for each message, so you don't need to set a deduplication ID when you send each message.
                    # https://docs.aws.amazon.com/sns/latest/dg/fifo-message-dedup.html
                    content = msg_context.message_content("sqs")
                    kwargs["MessageDeduplicationId"] = hashlib.sha256(
                        content.encode("utf-8")
                    ).hexdigest()

        elif msg_context.message_group_id:
            kwargs["MessageGroupId"] = msg_context.message_group_id

        # TODO: for message deduplication, we are using the underlying features of the SQS queue
        # however, SQS queue only deduplicate at the Queue level, where the SNS topic deduplicate on the topic level
        # we will need to implement this
        return kwargs