def test_deduplication_interval(self, sqs_create_queue, aws_sqs_client):
        fifo_queue_name = f"queue-{short_uid()}.fifo"
        queue_url = sqs_create_queue(QueueName=fifo_queue_name, Attributes={"FifoQueue": "true"})
        message_content = f"test{short_uid()}"
        message_content_duplicate = f"{message_content}-duplicate"
        message_content_half_time = f"{message_content}-half_time"
        dedup_id = f"fifo_dedup-{short_uid()}"
        group_id = f"fifo_group-{short_uid()}"
        result_send = aws_sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=message_content,
            MessageGroupId=group_id,
            MessageDeduplicationId=dedup_id,
        )
        time.sleep(3)
        aws_sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=message_content_duplicate,
            MessageGroupId=group_id,
            MessageDeduplicationId=dedup_id,
        )
        result_receive = retry(
            aws_sqs_client.receive_message, QueueUrl=queue_url, retries=5, sleep=1
        )
        aws_sqs_client.delete_message(
            QueueUrl=queue_url, ReceiptHandle=result_receive["Messages"][0]["ReceiptHandle"]
        )
        result_receive_duplicate = retry(
            aws_sqs_client.receive_message, QueueUrl=queue_url, retries=5, sleep=1
        )

        assert result_send.get("MessageId") == result_receive.get("Messages")[0].get("MessageId")
        assert result_send.get("MD5OfMessageBody") == result_receive.get("Messages")[0].get(
            "MD5OfBody"
        )
        assert "Messages" not in result_receive_duplicate

        dedup_id_2 = f"fifo_dedup-{short_uid()}"

        result_send = aws_sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=message_content,
            MessageGroupId=group_id,
            MessageDeduplicationId=dedup_id_2,
        )
        # ZZZZzzz...
        # Fifo Deduplication Interval is 5 minutes at minimum, + there seems no way to change it.
        # We give it a bit of leeway to avoid timing issues
        # https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/using-messagededuplicationid-property.html
        time.sleep(2)
        aws_sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=message_content_half_time,
            MessageGroupId=group_id,
            MessageDeduplicationId=dedup_id_2,
        )
        time.sleep(6 * 60)

        result_send_duplicate = aws_sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=message_content_duplicate,
            MessageGroupId=group_id,
            MessageDeduplicationId=dedup_id_2,
        )
        result_receive = aws_sqs_client.receive_message(QueueUrl=queue_url)
        aws_sqs_client.delete_message(
            QueueUrl=queue_url, ReceiptHandle=result_receive["Messages"][0]["ReceiptHandle"]
        )
        result_receive_duplicate = aws_sqs_client.receive_message(QueueUrl=queue_url)

        assert result_send.get("MessageId") == result_receive.get("Messages")[0].get("MessageId")
        assert result_send.get("MD5OfMessageBody") == result_receive.get("Messages")[0].get(
            "MD5OfBody"
        )
        assert result_send_duplicate.get("MessageId") == result_receive_duplicate.get("Messages")[
            0
        ].get("MessageId")
        assert result_send_duplicate.get("MD5OfMessageBody") == result_receive_duplicate.get(
            "Messages"
        )[0].get("MD5OfBody")