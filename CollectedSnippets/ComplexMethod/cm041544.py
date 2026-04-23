def test_fifo_list_messages_as_botocore_endpoint_url(
        self, sqs_create_queue, aws_client, aws_client_factory, monkeypatch, strategy, protocol
    ):
        monkeypatch.setattr(config, "SQS_ENDPOINT_STRATEGY", strategy)

        queue_url = sqs_create_queue(
            QueueName=f"queue-{short_uid()}.fifo",
            Attributes={
                "FifoQueue": "true",
                "ContentBasedDeduplication": "true",
            },
        )

        aws_client.sqs.send_message(QueueUrl=queue_url, MessageBody="message-1", MessageGroupId="1")
        aws_client.sqs.send_message(QueueUrl=queue_url, MessageBody="message-2", MessageGroupId="1")
        aws_client.sqs.send_message(QueueUrl=queue_url, MessageBody="message-3", MessageGroupId="2")

        # use the developer endpoint as boto client URL
        factory = aws_client_factory(endpoint_url="http://localhost:4566/_aws/sqs/messages")
        client = factory.sqs_query if protocol == "query" else factory.sqs
        # max messages is ignored
        response = client.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=1)

        assert len(response["Messages"]) == 3

        assert response["Messages"][0]["Body"] == "message-1"
        assert response["Messages"][1]["Body"] == "message-2"
        assert response["Messages"][2]["Body"] == "message-3"
        assert response["Messages"][0]["Attributes"]["ApproximateReceiveCount"] == "0"
        assert response["Messages"][1]["Attributes"]["ApproximateReceiveCount"] == "0"
        assert response["Messages"][2]["Attributes"]["ApproximateReceiveCount"] == "0"
        assert response["Messages"][0]["Attributes"]["MessageGroupId"] == "1"
        assert response["Messages"][1]["Attributes"]["MessageGroupId"] == "1"
        assert response["Messages"][2]["Attributes"]["MessageGroupId"] == "2"