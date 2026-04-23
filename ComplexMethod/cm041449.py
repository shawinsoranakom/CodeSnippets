def test_dlq_external_http_endpoint(
        self,
        sqs_create_queue,
        sqs_get_queue_arn,
        sns_create_http_endpoint,
        sns_allow_topic_sqs_queue,
        raw_message_delivery,
        aws_client,
    ):
        # Necessitate manual set up to allow external access to endpoint, only in local testing
        topic_arn, http_subscription_arn, endpoint_url, server = sns_create_http_endpoint(
            raw_message_delivery
        )

        dlq_url = sqs_create_queue()
        dlq_arn = sqs_get_queue_arn(dlq_url)

        sns_allow_topic_sqs_queue(
            sqs_queue_url=dlq_url, sqs_queue_arn=dlq_arn, sns_topic_arn=topic_arn
        )
        aws_client.sns.set_subscription_attributes(
            SubscriptionArn=http_subscription_arn,
            AttributeName="RedrivePolicy",
            AttributeValue=json.dumps({"deadLetterTargetArn": dlq_arn}),
        )
        assert poll_condition(
            lambda: len(server.log) >= 1,
            timeout=5,
        )
        sub_request, _ = server.log[0]
        payload = sub_request.get_json(force=True)
        assert payload["Type"] == "SubscriptionConfirmation"
        assert sub_request.headers["x-amz-sns-message-type"] == "SubscriptionConfirmation"

        subscribe_url = payload["SubscribeURL"]
        service_url, subscribe_url_path = payload["SubscribeURL"].rsplit("/", maxsplit=1)

        confirm_subscribe_request = requests.get(subscribe_url)
        confirm_subscribe = xmltodict.parse(confirm_subscribe_request.content)
        assert (
            confirm_subscribe["ConfirmSubscriptionResponse"]["ConfirmSubscriptionResult"][
                "SubscriptionArn"
            ]
            == http_subscription_arn
        )

        subscription_attributes = aws_client.sns.get_subscription_attributes(
            SubscriptionArn=http_subscription_arn
        )
        assert subscription_attributes["Attributes"]["PendingConfirmation"] == "false"

        server.stop()
        wait_for_port_closed(server.port)

        message = "test_dlq_external_http_endpoint"
        aws_client.sns.publish(TopicArn=topic_arn, Message=message)

        response = aws_client.sqs.receive_message(QueueUrl=dlq_url, WaitTimeSeconds=3)
        assert len(response["Messages"]) == 1, (
            f"invalid number of messages in DLQ response {response}"
        )

        if raw_message_delivery:
            assert response["Messages"][0]["Body"] == message
        else:
            received_message = json.loads(response["Messages"][0]["Body"])
            assert received_message["Type"] == "Notification"
            assert received_message["Message"] == message

        receipt_handle = response["Messages"][0]["ReceiptHandle"]
        aws_client.sqs.delete_message(QueueUrl=dlq_url, ReceiptHandle=receipt_handle)

        expected_unsubscribe_url = (
            f"{service_url}/?Action=Unsubscribe&SubscriptionArn={http_subscription_arn}"
        )

        unsub_request = requests.get(expected_unsubscribe_url)
        unsubscribe_confirmation = xmltodict.parse(unsub_request.content)
        assert "UnsubscribeResponse" in unsubscribe_confirmation

        response = aws_client.sqs.receive_message(QueueUrl=dlq_url, WaitTimeSeconds=2)
        # AWS doesn't send to the DLQ if the UnsubscribeConfirmation fails to be delivered
        assert "Messages" not in response or response["Messages"] == []