def test_publish_batch_messages_from_fifo_topic_to_fifo_queue(
        self,
        sns_create_topic,
        sqs_create_queue,
        sns_create_sqs_subscription,
        snapshot,
        content_based_deduplication,
        aws_client,
    ):
        topic_name = f"topic-{short_uid()}.fifo"
        queue_name = f"queue-{short_uid()}.fifo"
        topic_attributes = {"FifoTopic": "true"}
        queue_attributes = {"FifoQueue": "true"}
        if content_based_deduplication:
            topic_attributes["ContentBasedDeduplication"] = "true"
            queue_attributes["ContentBasedDeduplication"] = "true"

        topic_arn = sns_create_topic(
            Name=topic_name,
            Attributes=topic_attributes,
        )["TopicArn"]

        response = aws_client.sns.get_topic_attributes(TopicArn=topic_arn)
        snapshot.match("topic-attrs", response)

        queue_url = sqs_create_queue(
            QueueName=queue_name,
            Attributes=queue_attributes,
        )

        subscription = sns_create_sqs_subscription(topic_arn=topic_arn, queue_url=queue_url)
        subscription_arn = subscription["SubscriptionArn"]

        aws_client.sns.set_subscription_attributes(
            SubscriptionArn=subscription_arn,
            AttributeName="RawMessageDelivery",
            AttributeValue="true",
        )

        response = aws_client.sns.get_subscription_attributes(SubscriptionArn=subscription_arn)
        snapshot.match("sub-attrs-raw-true", response)
        message_group_id = "complexMessageGroupId"
        publish_batch_request_entries = [
            {
                "Id": "1",
                "MessageGroupId": message_group_id,
                "Message": "Test Message with two attributes",
                "Subject": "Subject",
                "MessageAttributes": {
                    "attr1": {"DataType": "Number", "StringValue": "99.12"},
                    "attr2": {"DataType": "Number", "StringValue": "109.12"},
                },
            },
            {
                "Id": "2",
                "MessageGroupId": message_group_id,
                "Message": "Test Message with one attribute",
                "Subject": "Subject",
                "MessageAttributes": {"attr1": {"DataType": "Number", "StringValue": "19.12"}},
            },
            {
                "Id": "3",
                "MessageGroupId": message_group_id,
                "Message": "Test Message without attribute",
                "Subject": "Subject",
            },
        ]

        if not content_based_deduplication:
            for index, message in enumerate(publish_batch_request_entries):
                message["MessageDeduplicationId"] = f"MessageDeduplicationId-{index}"

        publish_batch_response = aws_client.sns.publish_batch(
            TopicArn=topic_arn,
            PublishBatchRequestEntries=publish_batch_request_entries,
        )

        snapshot.match("publish-batch-response-fifo", publish_batch_response)

        assert "Successful" in publish_batch_response
        assert "Failed" in publish_batch_response

        for successful_resp in publish_batch_response["Successful"]:
            assert "Id" in successful_resp
            assert "MessageId" in successful_resp

        message_ids_received = set()
        messages = []

        def get_messages():
            # due to the random nature of receiving SQS messages, we need to consolidate a single object to match
            # MaxNumberOfMessages could return less than 3 messages
            sqs_response = aws_client.sqs.receive_message(
                QueueUrl=queue_url,
                MessageAttributeNames=["All"],
                AttributeNames=["All"],
                MaxNumberOfMessages=10,
                WaitTimeSeconds=1,
                VisibilityTimeout=10,
            )

            for _message in sqs_response["Messages"]:
                if _message["MessageId"] in message_ids_received:
                    continue

                message_ids_received.add(_message["MessageId"])
                messages.append(_message)
                aws_client.sqs.delete_message(
                    QueueUrl=queue_url, ReceiptHandle=_message["ReceiptHandle"]
                )

            assert len(messages) == 3

        retry(get_messages, retries=5, sleep=1)
        snapshot.match("messages", {"Messages": messages})

        publish_batch_response = aws_client.sns.publish_batch(
            TopicArn=topic_arn,
            PublishBatchRequestEntries=publish_batch_request_entries,
        )

        snapshot.match("republish-batch-response-fifo", publish_batch_response)
        get_deduplicated_messages = aws_client.sqs.receive_message(
            QueueUrl=queue_url,
            MessageAttributeNames=["All"],
            AttributeNames=["All"],
            MaxNumberOfMessages=10,
            WaitTimeSeconds=3,
            VisibilityTimeout=0,
        )
        # there should not be any messages here, as they are duplicate
        # see https://docs.aws.amazon.com/sns/latest/dg/fifo-message-dedup.html
        snapshot.match("duplicate-messages", get_deduplicated_messages)