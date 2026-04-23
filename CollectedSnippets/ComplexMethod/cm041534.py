def test_fifo_approx_number_of_messages(self, sqs_create_queue, aws_sqs_client):
        queue_url = sqs_create_queue(
            QueueName=f"queue-{short_uid()}.fifo",
            Attributes={
                "FifoQueue": "true",
                "ContentBasedDeduplication": "true",
            },
        )

        assert get_qsize(aws_sqs_client, queue_url) == 0

        aws_sqs_client.send_message(QueueUrl=queue_url, MessageBody="g1-m1", MessageGroupId="1")
        aws_sqs_client.send_message(QueueUrl=queue_url, MessageBody="g1-m2", MessageGroupId="1")
        aws_sqs_client.send_message(QueueUrl=queue_url, MessageBody="g1-m3", MessageGroupId="1")
        aws_sqs_client.send_message(QueueUrl=queue_url, MessageBody="g2-m1", MessageGroupId="2")
        aws_sqs_client.send_message(QueueUrl=queue_url, MessageBody="g3-m1", MessageGroupId="3")

        assert get_qsize(aws_sqs_client, queue_url) == 5

        response = aws_sqs_client.receive_message(
            QueueUrl=queue_url, MaxNumberOfMessages=4, WaitTimeSeconds=1
        )

        if is_aws_cloud():
            time.sleep(5)

        assert get_qsize(aws_sqs_client, queue_url) == 1

        for message in response["Messages"]:
            aws_sqs_client.delete_message(
                QueueUrl=queue_url, ReceiptHandle=message["ReceiptHandle"]
            )

        if is_aws_cloud():
            time.sleep(5)

        assert get_qsize(aws_sqs_client, queue_url) == 1