def test_publish_get_delete_message_batch(self, sqs_create_queue, aws_sqs_client):
        message_count = 10
        queue_name = f"queue-{short_uid()}"
        queue_url = sqs_create_queue(QueueName=queue_name)

        message_batch = [
            {
                "Id": f"message-{i}",
                "MessageBody": f"messageBody-{i}",
            }
            for i in range(message_count)
        ]

        result_send_batch = aws_sqs_client.send_message_batch(
            QueueUrl=queue_url, Entries=message_batch
        )
        successful = result_send_batch["Successful"]
        assert len(successful) == len(message_batch)

        result_recv = []
        i = 0
        while len(result_recv) < message_count and i < message_count:
            result = aws_sqs_client.receive_message(
                QueueUrl=queue_url, MaxNumberOfMessages=message_count
            ).get("Messages", [])
            if result:
                result_recv.extend(result)
                i += 1

        assert len(result_recv) == message_count

        ids_sent = set()
        ids_received = set()
        for i in range(message_count):
            ids_sent.add(successful[i]["MessageId"])
            ids_received.add(result_recv[i]["MessageId"])

        assert ids_sent == ids_received

        delete_entries = [
            {"Id": message["MessageId"], "ReceiptHandle": message["ReceiptHandle"]}
            for message in result_recv
        ]
        aws_sqs_client.delete_message_batch(QueueUrl=queue_url, Entries=delete_entries)
        confirmation = aws_sqs_client.receive_message(
            QueueUrl=queue_url, MaxNumberOfMessages=message_count
        )
        assert "Messages" not in confirmation or confirmation["Messages"] == []