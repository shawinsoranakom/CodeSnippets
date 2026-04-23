def test_batch_send_with_invalid_char_should_succeed(self, sqs_create_queue, aws_sqs_client):
        # issue 4135
        queue_url = sqs_create_queue()

        batch = []
        for i in range(0, 9):
            batch.append({"Id": str(i), "MessageBody": str(i)})
        batch.append({"Id": "9", "MessageBody": "\x01"})

        result_send = aws_sqs_client.send_message_batch(QueueUrl=queue_url, Entries=batch)

        # check the one failed message
        assert len(result_send["Failed"]) == 1
        failed = result_send["Failed"][0]
        assert failed["Id"] == "9"
        assert failed["Code"] == "InvalidMessageContents"

        # check successful message bodies
        messages = []

        def collect_messages():
            response = aws_sqs_client.receive_message(
                QueueUrl=queue_url, MaxNumberOfMessages=10, WaitTimeSeconds=1
            )
            messages.extend(response.get("Messages", []))
            return len(messages)

        assert poll_condition(lambda: collect_messages() >= 9, timeout=10), (
            f"gave up waiting messages, got {len(messages)} from 9"
        )

        bodies = {message["Body"] for message in messages}
        assert bodies == {"0", "1", "2", "3", "4", "5", "6", "7", "8"}