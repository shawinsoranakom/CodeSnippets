def test_subscription_tokens_can_retrospect(
        self,
        sns_create_topic,
        sns_subscription,
        sns_create_http_endpoint,
        aws_client,
        account_id,
        region_name,
    ):
        sns_store = SnsProvider.get_store(account_id, region_name)
        # clean up the saved tokens
        sns_store.subscription_tokens.clear()

        message = "Good news everyone!"
        # Necessitate manual set up to allow external access to endpoint, only in local testing
        topic_arn, subscription_arn, endpoint_url, server = sns_create_http_endpoint()
        assert poll_condition(
            lambda: len(server.log) >= 1,
            timeout=5,
        )
        sub_request, _ = server.log[0]
        payload = sub_request.get_json(force=True)
        assert payload["Type"] == "SubscriptionConfirmation"
        token = payload["Token"]
        server.clear()

        # we won't confirm the subscription, to simulate an external provider that wouldn't be able to access LocalStack
        # try to access the internal to confirm the Token is there
        tokens_base_url = config.internal_service_url() + SUBSCRIPTION_TOKENS_ENDPOINT
        api_contents = requests.get(f"{tokens_base_url}/{subscription_arn}").json()
        assert api_contents["subscription_token"] == token
        assert api_contents["subscription_arn"] == subscription_arn

        # try to send a message to an unconfirmed subscription, assert that the message isn't received
        aws_client.sns.publish(Message=message, TopicArn=topic_arn)

        assert poll_condition(
            lambda: len(server.log) == 0,
            timeout=1,
        )

        aws_client.sns.confirm_subscription(TopicArn=topic_arn, Token=token)
        aws_client.sns.publish(Message=message, TopicArn=topic_arn)
        assert poll_condition(
            lambda: len(server.log) == 1,
            timeout=2,
        )

        wrong_sub_arn = subscription_arn.replace(
            region_name,
            "il-central-1" if region_name != "il-central-1" else "me-south-1",
        )
        wrong_region_req = requests.get(f"{tokens_base_url}/{wrong_sub_arn}")
        assert wrong_region_req.status_code == 404
        assert wrong_region_req.json() == {
            "error": "The provided SubscriptionARN is not found",
            "subscription_arn": wrong_sub_arn,
        }

        # Ensure proper error is raised with wrong ARN
        incorrect_arn_req = requests.get(f"{tokens_base_url}/randomarnhere")
        assert incorrect_arn_req.status_code == 400
        assert incorrect_arn_req.json() == {
            "error": "The provided SubscriptionARN is invalid",
            "subscription_arn": "randomarnhere",
        }