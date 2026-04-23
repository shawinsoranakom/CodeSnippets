def test_list_messages_as_json(
        self, sqs_create_queue, monkeypatch, aws_client, account_id, strategy
    ):
        monkeypatch.setattr(config, "SQS_ENDPOINT_STRATEGY", strategy)

        queue_url = sqs_create_queue()

        aws_client.sqs.send_message(QueueUrl=queue_url, MessageBody="message-1")
        aws_client.sqs.send_message(QueueUrl=queue_url, MessageBody="message-2")

        response = requests.get(
            "http://localhost:4566/_aws/sqs/messages",
            params={"QueueUrl": queue_url},
            headers={"Accept": "application/json"},
        )
        doc = response.json()

        messages = doc["ReceiveMessageResponse"]["ReceiveMessageResult"]["Message"]

        assert len(messages) == 2
        assert messages[0]["Body"] == "message-1"
        assert messages[0]["MD5OfBody"] == "3d6b824fd8c1520e9a047d21fee6fb1f"

        assert messages[1]["Body"] == "message-2"
        assert messages[1]["MD5OfBody"] == "95ef155b66299d14edf7ed57c468c13b"

        # make sure attributes are returned
        attributes = {a["Name"]: a["Value"] for a in messages[0]["Attribute"]}
        assert attributes["SenderId"] == account_id
        assert "ApproximateReceiveCount" in attributes
        assert "ApproximateFirstReceiveTimestamp" in attributes
        assert "SentTimestamp" in attributes