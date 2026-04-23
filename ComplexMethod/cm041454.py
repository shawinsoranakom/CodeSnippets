def test_filter_policy_on_message_body(
        self,
        sqs_create_queue,
        sns_create_topic,
        sns_create_sqs_subscription,
        snapshot,
        raw_message_delivery,
        aws_client,
    ):
        topic_arn = sns_create_topic()["TopicArn"]
        queue_url = sqs_create_queue()
        subscription = sns_create_sqs_subscription(topic_arn=topic_arn, queue_url=queue_url)
        subscription_arn = subscription["SubscriptionArn"]
        # see https://aws.amazon.com/blogs/compute/introducing-payload-based-message-filtering-for-amazon-sns/
        nested_filter_policy = {
            "object": {
                "key": [{"prefix": "auto-"}, "hardcodedvalue"],
                "nested_key": [{"exists": False}],
            },
            "test": [{"exists": False}],
        }

        aws_client.sns.set_subscription_attributes(
            SubscriptionArn=subscription_arn,
            AttributeName="FilterPolicyScope",
            AttributeValue="MessageBody",
        )

        aws_client.sns.set_subscription_attributes(
            SubscriptionArn=subscription_arn,
            AttributeName="FilterPolicy",
            AttributeValue=json.dumps(nested_filter_policy),
        )

        if raw_message_delivery:
            aws_client.sns.set_subscription_attributes(
                SubscriptionArn=subscription_arn,
                AttributeName="RawMessageDelivery",
                AttributeValue="true",
            )

        response = aws_client.sqs.receive_message(
            QueueUrl=queue_url, VisibilityTimeout=0, WaitTimeSeconds=1
        )
        snapshot.match("recv-init", response)
        # assert there are no messages in the queue
        assert "Messages" not in response or response["Messages"] == []

        # publish messages that satisfies the filter policy, assert that messages are received
        messages = [
            {"object": {"key": "auto-test"}},
            {"object": {"key": "hardcodedvalue"}},
        ]
        for i, message in enumerate(messages):
            aws_client.sns.publish(
                TopicArn=topic_arn,
                Message=json.dumps(message),
            )

            response = aws_client.sqs.receive_message(
                QueueUrl=queue_url,
                VisibilityTimeout=0,
                WaitTimeSeconds=5 if is_aws_cloud() else 2,
            )
            snapshot.match(f"recv-passed-msg-{i}", response)
            receipt_handle = response["Messages"][0]["ReceiptHandle"]
            aws_client.sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)

        # publish messages that do not satisfy the filter policy, assert those messages are not received
        messages = [
            {"object": {"key": "test-auto"}},
            {"object": {"key": "auto-test"}, "test": "just-exists"},
            {"object": {"key": "auto-test", "nested_key": "just-exists"}},
            {"object": {"test": "auto-test"}},
            {"test": "auto-test"},
        ]
        for message in messages:
            aws_client.sns.publish(
                TopicArn=topic_arn,
                Message=json.dumps(message),
            )

        response = aws_client.sqs.receive_message(
            QueueUrl=queue_url, VisibilityTimeout=0, WaitTimeSeconds=5 if is_aws_cloud() else 2
        )
        # assert there are no messages in the queue
        assert "Messages" not in response or response["Messages"] == []

        # publish message that does not satisfy the filter policy as it's not even JSON, or not a JSON object
        message = "Regular string message"
        aws_client.sns.publish(
            TopicArn=topic_arn,
            Message=message,
        )
        aws_client.sns.publish(
            TopicArn=topic_arn,
            Message=json.dumps(message),  # send it JSON encoded, but not an object
        )

        response = aws_client.sqs.receive_message(
            QueueUrl=queue_url, VisibilityTimeout=0, WaitTimeSeconds=2
        )
        # assert there are no messages in the queue
        assert "Messages" not in response or response["Messages"] == []