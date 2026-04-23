def test_multiple_subscriptions_http_endpoint(
        self, sns_create_topic, sns_subscription, aws_client
    ):
        # create a topic
        topic_arn = sns_create_topic()["TopicArn"]

        # build fake http server endpoints
        _requests = queue.Queue()

        # create HTTP endpoint and connect it to SNS topic
        def handler(_request):
            _requests.put(_request)
            return Response(status=429)

        number_of_endpoints = 4

        servers = []
        try:
            for _ in range(number_of_endpoints):
                server = HTTPServer()
                server.start()
                servers.append(server)
                server.expect_request("/").respond_with_handler(handler)
                http_endpoint = server.url_for("/")
                wait_for_port_open(http_endpoint)

                sns_subscription(TopicArn=topic_arn, Protocol="http", Endpoint=http_endpoint)

            # fetch subscription information
            subscription_list = aws_client.sns.list_subscriptions_by_topic(TopicArn=topic_arn)
            assert subscription_list["ResponseMetadata"]["HTTPStatusCode"] == 200
            assert len(subscription_list["Subscriptions"]) == number_of_endpoints, (
                f"unexpected number of subscriptions {subscription_list}"
            )

            tokens = []
            for _ in range(number_of_endpoints):
                request = _requests.get(timeout=2)
                request_data = request.get_json(True)
                tokens.append(request_data["Token"])
                assert request_data["TopicArn"] == topic_arn

            with pytest.raises(queue.Empty):
                # make sure only four requests are received
                _requests.get(timeout=1)

            # assert the first subscription is pending confirmation
            sub_1 = subscription_list["Subscriptions"][0]
            sub_1_attrs = aws_client.sns.get_subscription_attributes(
                SubscriptionArn=sub_1["SubscriptionArn"]
            )
            assert sub_1_attrs["Attributes"]["PendingConfirmation"] == "true"

            # assert the second subscription is pending confirmation
            sub_2 = subscription_list["Subscriptions"][1]
            sub_2_attrs = aws_client.sns.get_subscription_attributes(
                SubscriptionArn=sub_2["SubscriptionArn"]
            )
            assert sub_2_attrs["Attributes"]["PendingConfirmation"] == "true"

            # confirm the first subscription
            response = aws_client.sns.confirm_subscription(TopicArn=topic_arn, Token=tokens[0])
            # assert the confirmed subscription is the first one
            assert response["SubscriptionArn"] == sub_1["SubscriptionArn"]

            # assert the first subscription is confirmed
            sub_1_attrs = aws_client.sns.get_subscription_attributes(
                SubscriptionArn=sub_1["SubscriptionArn"]
            )
            assert sub_1_attrs["Attributes"]["PendingConfirmation"] == "false"

            # assert the second subscription is NOT confirmed
            sub_2_attrs = aws_client.sns.get_subscription_attributes(
                SubscriptionArn=sub_2["SubscriptionArn"]
            )
            assert sub_2_attrs["Attributes"]["PendingConfirmation"] == "true"

        finally:
            subscription_list = aws_client.sns.list_subscriptions_by_topic(TopicArn=topic_arn)
            for subscription in subscription_list["Subscriptions"]:
                aws_client.sns.unsubscribe(SubscriptionArn=subscription["SubscriptionArn"])
            for server in servers:
                server.stop()