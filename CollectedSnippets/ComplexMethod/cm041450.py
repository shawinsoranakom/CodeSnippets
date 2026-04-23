def test_cross_account_access(self, sns_primary_client, sns_secondary_client, sns_create_topic):
        # Cross-account access is supported for below operations.
        # This list is taken from ActionName param of the AddPermissions operation
        #
        # - GetTopicAttributes
        # - SetTopicAttributes
        # - AddPermission
        # - RemovePermission
        # - Publish
        # - Subscribe
        # - ListSubscriptionsByTopic
        # - DeleteTopic

        topic_name = f"topic-{short_uid()}"
        # sns_create_topic uses the primary client by default
        topic_arn = sns_create_topic(Name=topic_name)["TopicArn"]

        assert sns_secondary_client.set_topic_attributes(
            TopicArn=topic_arn, AttributeName="DisplayName", AttributeValue="xenon"
        )

        response = sns_secondary_client.get_topic_attributes(TopicArn=topic_arn)
        assert response["Attributes"]["DisplayName"] == "xenon"

        assert sns_secondary_client.add_permission(
            TopicArn=topic_arn,
            Label="foo",
            AWSAccountId=["666666666666"],
            ActionName=["AddPermission"],
        )
        assert sns_secondary_client.remove_permission(TopicArn=topic_arn, Label="foo")

        assert sns_secondary_client.publish(TopicArn=topic_arn, Message="hello world")

        subscription_arn = sns_secondary_client.subscribe(
            TopicArn=topic_arn, Protocol="email", Endpoint="devil@hell.com"
        )["SubscriptionArn"]

        response = sns_secondary_client.list_subscriptions_by_topic(TopicArn=topic_arn)
        subscriptions = [s["SubscriptionArn"] for s in response["Subscriptions"]]
        assert subscription_arn in subscriptions

        response = sns_primary_client.set_subscription_attributes(
            SubscriptionArn=subscription_arn,
            AttributeName="RawMessageDelivery",
            AttributeValue="true",
        )
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
        response = sns_primary_client.get_subscription_attributes(SubscriptionArn=subscription_arn)
        assert response["Attributes"]["RawMessageDelivery"] == "true"

        assert sns_secondary_client.delete_topic(TopicArn=topic_arn)