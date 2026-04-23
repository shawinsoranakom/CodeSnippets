def test_send_receive_message(self, sqs_queue, aws_sqs_client):
        send_result = aws_sqs_client.send_message(QueueUrl=sqs_queue, MessageBody="message")

        assert send_result["MessageId"]
        assert send_result["MD5OfMessageBody"] == "78e731027d8fd50ed642340b7c9a63b3"
        # TODO: other attributes

        receive_result = aws_sqs_client.receive_message(QueueUrl=sqs_queue)

        assert len(receive_result["Messages"]) == 1
        message = receive_result["Messages"][0]

        assert message["ReceiptHandle"]
        assert message["Body"] == "message"
        assert message["MessageId"] == send_result["MessageId"]
        assert message["MD5OfBody"] == send_result["MD5OfMessageBody"]