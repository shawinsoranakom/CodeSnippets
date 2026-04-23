def test_list_subscriptions_by_topic_pagination(
        self, sns_create_topic, sns_subscription, snapshot, aws_client
    ):
        # ordering of the listing seems to be not consistent, so we can transform its value
        snapshot.add_transformers_list(
            [
                snapshot.transform.key_value("Endpoint"),
                snapshot.transform.key_value("NextToken"),
            ]
        )

        base_phone_number = "+12312312"
        topic_arn = sns_create_topic()["TopicArn"]
        for phone_suffix in range(101):
            phone_number = f"{base_phone_number}{phone_suffix}"
            sns_subscription(TopicArn=topic_arn, Protocol="sms", Endpoint=phone_number)

        response = aws_client.sns.list_subscriptions_by_topic(TopicArn=topic_arn)
        # not snapshotting the results, it contains 100 entries
        assert "NextToken" in response
        # seems to be b64 encoded
        assert base64.b64decode(response["NextToken"])
        assert len(response["Subscriptions"]) == 100
        # keep the page 1 subscriptions ARNs
        page_1_subs = {sub["SubscriptionArn"] for sub in response["Subscriptions"]}

        response = aws_client.sns.list_subscriptions_by_topic(
            TopicArn=topic_arn, NextToken=response["NextToken"]
        )
        snapshot.match("list-sub-per-topic-page-2", response)
        assert "NextToken" not in response
        assert len(response["Subscriptions"]) == 1
        # assert that the last Subscription is not present in page 1
        assert response["Subscriptions"][0]["SubscriptionArn"] not in page_1_subs

        response = aws_client.sns.list_subscriptions()
        # not snapshotting because there might be subscriptions outside the topic, this is all the requester subs
        assert "NextToken" in response
        assert len(response["Subscriptions"]) <= 100