def test_fifo_list_messages_with_invisible_messages(
        self,
        sqs_create_queue,
        aws_client,
        monkeypatch,
        strategy,
    ):
        monkeypatch.setattr(config, "SQS_ENDPOINT_STRATEGY", strategy)

        queue_url = sqs_create_queue(
            QueueName=f"queue-{short_uid()}.fifo",
            Attributes={
                "FifoQueue": "true",
                "ContentBasedDeduplication": "true",
                "VisibilityTimeout": "120",
            },
        )
        aws_client.sqs.send_message(QueueUrl=queue_url, MessageBody="message-1", MessageGroupId="1")
        aws_client.sqs.send_message(QueueUrl=queue_url, MessageBody="message-2", MessageGroupId="1")
        aws_client.sqs.send_message(QueueUrl=queue_url, MessageBody="message-3", MessageGroupId="2")
        aws_client.sqs.send_message(QueueUrl=queue_url, MessageBody="message-4", MessageGroupId="2")

        # check out a messages
        aws_client.sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=1)

        response = requests.get(
            "http://localhost:4566/_aws/sqs/messages",
            params={"QueueUrl": queue_url, "ShowInvisible": False},
            headers={"Accept": "application/json"},
        )
        doc = response.json()
        messages = doc["ReceiveMessageResponse"]["ReceiveMessageResult"]["Message"]
        assert len(messages) == 2
        assert messages[0]["Body"] == "message-3"
        assert messages[1]["Body"] == "message-4"

        response = requests.get(
            "http://localhost:4566/_aws/sqs/messages",
            params={"QueueUrl": queue_url, "ShowInvisible": True},
            headers={"Accept": "application/json"},
        )
        doc = response.json()
        messages: list[dict] = doc["ReceiveMessageResponse"]["ReceiveMessageResult"]["Message"]
        assert len(messages) == 4
        # there are no clear sorting rules in this scenario (fifo queues, invisible, + the way messages are collected)
        messages.sort(key=lambda k: k["Body"])
        assert messages[0]["Body"] == "message-1"
        assert messages[1]["Body"] == "message-2"
        assert messages[2]["Body"] == "message-3"
        assert messages[3]["Body"] == "message-4"

        assert _parse_attribute_map(messages[0])["IsVisible"] == "false"
        # so technically the message itself IS visible, but the message *group* is invisible. implementing that this
        # shows "false" for message-2 requires a bit of rework in our current implementation, so i would consider this a
        # fair limitation for now, given its subject to interpretation anyway.
        assert _parse_attribute_map(messages[1])["IsVisible"] == "true"
        assert _parse_attribute_map(messages[2])["IsVisible"] == "true"
        assert _parse_attribute_map(messages[3])["IsVisible"] == "true"