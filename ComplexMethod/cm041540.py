def test_receive_message_message_attribute_names_filters(
        self, sqs_create_queue, snapshot, aws_sqs_client
    ):
        """
        Receive message allows a list of filters to be passed with MessageAttributeNames. See:
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs.html#SQS.Client.receive_message
        """
        queue_url = sqs_create_queue(Attributes={"VisibilityTimeout": "0"})

        response = aws_sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody="msg",
            MessageAttributes={
                "Help.Me": {"DataType": "String", "StringValue": "Me"},
                "Hello": {"DataType": "String", "StringValue": "There"},
                "General": {"DataType": "String", "StringValue": "Kenobi"},
            },
        )
        assert snapshot.match("send_message_response", response)

        def receive_message(message_attribute_names):
            return aws_sqs_client.receive_message(
                QueueUrl=queue_url,
                WaitTimeSeconds=5,
                MessageAttributeNames=message_attribute_names,
            )

        # test empty filter
        response = receive_message([])
        # do the first check with the entire response
        assert snapshot.match("empty_filter", response)

        # test "All"
        response = receive_message(["All"])
        assert snapshot.match("all_name", response)

        # test "*"
        response = receive_message(["*"])
        assert snapshot.match("all_wildcard_asterisk", response["Messages"][0])

        # test ".*"
        response = receive_message([".*"])
        assert snapshot.match("all_wildcard", response["Messages"][0])

        # test only non-existent names
        response = receive_message(["Foo", "Help"])
        assert snapshot.match("only_non_existing_names", response["Messages"][0])

        # test all existing
        response = receive_message(["Hello", "General"])
        assert snapshot.match("only_existing", response["Messages"][0])

        # test existing and non-existing
        response = receive_message(["Foo", "Hello"])
        assert snapshot.match("existing_and_non_existing", response["Messages"][0])

        # test prefix filters
        response = receive_message(["Hel.*"])
        assert snapshot.match("prefix_filter", response["Messages"][0])

        # test illegal names
        response = receive_message(["AWS."])
        assert snapshot.match("illegal_name_1", response)
        response = receive_message(["..foo"])
        assert snapshot.match("illegal_name_2", response)