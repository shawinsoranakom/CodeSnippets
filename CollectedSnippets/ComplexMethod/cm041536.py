def test_dead_letter_queue_chain(
        self, sqs_create_queue, aws_sqs_client, account_id, region_name
    ):
        # test a chain of 3 queues, with DLQ flow q1 -> q2 -> q3

        # create queues
        queue_names = [f"q-{short_uid()}", f"q-{short_uid()}", f"q-{short_uid()}"]
        queue_urls = []

        for queue_name in queue_names:
            url = sqs_create_queue(QueueName=queue_name, Attributes={"VisibilityTimeout": "0"})
            queue_urls.append(url)

        # set redrive policies
        for idx, queue_name in enumerate(queue_names[:2]):
            policy = {
                "deadLetterTargetArn": arns.sqs_queue_arn(
                    queue_names[idx + 1],
                    account_id=account_id,
                    region_name=region_name,
                ),
                "maxReceiveCount": 1,
            }
            aws_sqs_client.set_queue_attributes(
                QueueUrl=queue_urls[idx],
                Attributes={"RedrivePolicy": json.dumps(policy), "VisibilityTimeout": "0"},
            )

        def _retry_receive(q_url):
            def _receive():
                _result = aws_sqs_client.receive_message(QueueUrl=q_url)
                assert _result.get("Messages")
                return _result

            return retry(_receive, sleep=1, retries=5)

        # send message
        result = aws_sqs_client.send_message(QueueUrl=queue_urls[0], MessageBody="test")
        # retrieve message from q1
        result = _retry_receive(queue_urls[0])
        assert len(result.get("Messages")) == 1
        # Wait for VisibilityTimeout to expire
        time.sleep(1.1)
        # retrieve message from q1 again -> no message, should go to DLQ q2
        result = aws_sqs_client.receive_message(QueueUrl=queue_urls[0])
        assert not result.get("Messages")
        # retrieve message from q2
        result = _retry_receive(queue_urls[1])
        assert len(result.get("Messages")) == 1
        # retrieve message from q2 again -> no message, should go to DLQ q3
        result = aws_sqs_client.receive_message(QueueUrl=queue_urls[1])
        assert not result.get("Messages")
        # retrieve message from q3
        result = _retry_receive(queue_urls[2])
        assert len(result.get("Messages")) == 1