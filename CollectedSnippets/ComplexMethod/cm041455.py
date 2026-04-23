def test_filter_policy_on_message_body_dot_attribute(
        self,
        sqs_create_queue,
        sns_create_topic,
        sns_create_sqs_subscription,
        snapshot,
        aws_client,
    ):
        topic_arn = sns_create_topic()["TopicArn"]
        queue_url = sqs_create_queue()
        subscription = sns_create_sqs_subscription(topic_arn=topic_arn, queue_url=queue_url)
        subscription_arn = subscription["SubscriptionArn"]

        nested_filter_policy = json.dumps(
            {
                "object.nested": ["string.value"],
            }
        )

        aws_client.sns.set_subscription_attributes(
            SubscriptionArn=subscription_arn,
            AttributeName="FilterPolicyScope",
            AttributeValue="MessageBody",
        )

        aws_client.sns.set_subscription_attributes(
            SubscriptionArn=subscription_arn,
            AttributeName="FilterPolicy",
            AttributeValue=nested_filter_policy,
        )

        def get_filter_policy():
            subscription_attrs = aws_client.sns.get_subscription_attributes(
                SubscriptionArn=subscription_arn
            )
            return subscription_attrs["Attributes"]["FilterPolicy"]

        # wait for the new filter policy to be in effect
        poll_condition(lambda: get_filter_policy() == nested_filter_policy, timeout=4)

        response = aws_client.sqs.receive_message(
            QueueUrl=queue_url, VisibilityTimeout=0, WaitTimeSeconds=1
        )
        snapshot.match("recv-init", response)
        # assert there are no messages in the queue
        assert "Messages" not in response or response["Messages"] == []

        def _verify_and_snapshot_sqs_messages(msg_to_send: list[dict], snapshot_prefix: str):
            for i, _message in enumerate(msg_to_send):
                aws_client.sns.publish(
                    TopicArn=topic_arn,
                    Message=json.dumps(_message),
                )

                _response = aws_client.sqs.receive_message(
                    QueueUrl=queue_url,
                    VisibilityTimeout=0,
                    WaitTimeSeconds=5 if is_aws_cloud() else 2,
                )
                snapshot.match(f"{snapshot_prefix}-{i}", _response)
                receipt_handle = _response["Messages"][0]["ReceiptHandle"]
                aws_client.sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)

        # publish messages that satisfies the filter policy, assert that messages are received
        messages = [
            {"object": {"nested": "string.value"}},
            {"object.nested": "string.value"},
        ]
        _verify_and_snapshot_sqs_messages(messages, snapshot_prefix="recv-nested-msg")

        # publish messages that do not satisfy the filter policy, assert those messages are not received
        messages = [
            {"object": {"nested": "test-auto"}},
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

        # assert with more nesting
        deep_nested_filter_policy = json.dumps(
            {
                "object.nested.test": ["string.value"],
            }
        )

        aws_client.sns.set_subscription_attributes(
            SubscriptionArn=subscription_arn,
            AttributeName="FilterPolicy",
            AttributeValue=deep_nested_filter_policy,
        )
        # wait for the new filter policy to be in effect
        poll_condition(lambda: get_filter_policy() == deep_nested_filter_policy, timeout=4)

        messages = [
            {"object": {"nested": {"test": "string.value"}}},
            {"object.nested.test": "string.value"},
            {"object.nested": {"test": "string.value"}},
            {"object": {"nested.test": "string.value"}},
        ]
        _verify_and_snapshot_sqs_messages(messages, snapshot_prefix="recv-deep-nested-msg")
        # publish messages that do not satisfy the filter policy, assert those messages are not received
        messages = [
            {"object": {"nested": {"test": "string.notvalue"}}},
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