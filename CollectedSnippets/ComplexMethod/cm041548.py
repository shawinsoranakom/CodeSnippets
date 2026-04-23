def test_list_messages_with_delayed_messages(
        self, sqs_create_queue, aws_client, monkeypatch, strategy
    ):
        monkeypatch.setattr(config, "SQS_ENDPOINT_STRATEGY", strategy)

        queue_url = sqs_create_queue()

        aws_client.sqs.send_message(QueueUrl=queue_url, MessageBody="message-1")
        aws_client.sqs.send_message(QueueUrl=queue_url, MessageBody="message-2", DelaySeconds=10)
        aws_client.sqs.send_message(QueueUrl=queue_url, MessageBody="message-3", DelaySeconds=10)

        response = requests.get(
            "http://localhost:4566/_aws/sqs/messages",
            params={"QueueUrl": queue_url, "ShowDelayed": False},
            headers={"Accept": "application/json"},
        )
        doc = response.json()
        messages = doc["ReceiveMessageResponse"]["ReceiveMessageResult"]["Message"]
        assert messages["Body"] == "message-1"

        response = requests.get(
            "http://localhost:4566/_aws/sqs/messages",
            params={"QueueUrl": queue_url, "ShowDelayed": True},
            headers={"Accept": "application/json"},
        )
        doc = response.json()
        messages = doc["ReceiveMessageResponse"]["ReceiveMessageResult"]["Message"]
        assert len(messages) == 3
        messages.sort(key=lambda k: k["Body"])
        assert messages[0]["Body"] == "message-1"
        assert messages[1]["Body"] == "message-2"
        assert messages[2]["Body"] == "message-3"

        assert _parse_attribute_map(messages[0])["IsDelayed"] == "false"
        assert _parse_attribute_map(messages[1])["IsDelayed"] == "true"
        assert _parse_attribute_map(messages[2])["IsDelayed"] == "true"