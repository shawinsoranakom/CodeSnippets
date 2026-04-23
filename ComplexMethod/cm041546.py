def test_list_messages_with_invisible_messages(
        self, sqs_create_queue, aws_client, monkeypatch, strategy
    ):
        monkeypatch.setattr(config, "SQS_ENDPOINT_STRATEGY", strategy)

        queue_url = sqs_create_queue()

        aws_client.sqs.send_message(QueueUrl=queue_url, MessageBody="message-1")
        aws_client.sqs.send_message(QueueUrl=queue_url, MessageBody="message-2")
        aws_client.sqs.send_message(QueueUrl=queue_url, MessageBody="message-3")

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
        assert messages[0]["Body"] == "message-2"
        assert messages[1]["Body"] == "message-3"

        response = requests.get(
            "http://localhost:4566/_aws/sqs/messages",
            params={"QueueUrl": queue_url, "ShowInvisible": True},
            headers={"Accept": "application/json"},
        )
        doc = response.json()
        messages = doc["ReceiveMessageResponse"]["ReceiveMessageResult"]["Message"]
        assert len(messages) == 3
        assert messages[0]["Body"] == "message-1"
        assert messages[1]["Body"] == "message-2"
        assert messages[2]["Body"] == "message-3"

        assert _parse_attribute_map(messages[0])["IsVisible"] == "false"
        assert _parse_attribute_map(messages[1])["IsVisible"] == "true"
        assert _parse_attribute_map(messages[2])["IsVisible"] == "true"