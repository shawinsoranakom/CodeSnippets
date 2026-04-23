def test_endpoint_strategy_with_multi_region(
        self,
        strategy,
        sqs_http_client,
        aws_client_factory,
        aws_http_client_factory,
        monkeypatch,
        cleanups,
    ):
        monkeypatch.setattr(config, "SQS_ENDPOINT_STRATEGY", strategy)

        queue_name = f"test-queue-{short_uid()}"
        region1 = "us-west-1"
        region2 = "eu-north-1"

        sqs_region1 = aws_client_factory(region_name=region1).sqs
        sqs_region2 = aws_client_factory(region_name=region2).sqs

        queue_region1 = sqs_region1.create_queue(QueueName=queue_name)["QueueUrl"]
        cleanups.append(lambda: sqs_region1.delete_queue(QueueUrl=queue_region1))
        queue_region2 = sqs_region2.create_queue(QueueName=queue_name)["QueueUrl"]
        cleanups.append(lambda: sqs_region2.delete_queue(QueueUrl=queue_region2))

        if strategy == "off":
            assert queue_region1 == queue_region2
        else:
            assert queue_region1 != queue_region2
            assert region2 in queue_region2
            # us-east-1 is the default region, so it's not necessarily part of the queue URL

        client_region1 = aws_http_client_factory("sqs_query", region1)
        client_region2 = aws_http_client_factory("sqs_query", region2)

        response = client_region1.get(
            queue_region1, params={"Action": "SendMessage", "MessageBody": "foobar"}
        )
        assert response.ok

        # shouldn't return anything
        response = client_region2.get(
            queue_region2, params={"Action": "ReceiveMessage", "VisibilityTimeout": "0"}
        )
        assert response.ok
        assert "foobar" not in response.text

        # should return the message
        response = client_region1.get(
            queue_region1, params={"Action": "ReceiveMessage", "VisibilityTimeout": "0"}
        )
        assert response.ok
        assert "foobar" in response.text