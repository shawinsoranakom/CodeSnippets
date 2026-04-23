def test_publish_to_platform_endpoint_can_retrospect(
        self,
        sns_create_topic,
        sns_subscription,
        sns_create_platform_application,
        aws_client,
        account_id,
        region_name,
        secondary_region_name,
        platform_credentials,
    ):
        platform = "APNS"
        client_id, client_secret = platform_credentials
        attributes = {"PlatformPrincipal": client_id, "PlatformCredential": client_secret}
        sns_backend = SnsProvider.get_store(account_id, region_name)
        # clean up the saved messages
        sns_backend_endpoint_arns = list(sns_backend.platform_endpoint_messages.keys())
        for saved_endpoint_arn in sns_backend_endpoint_arns:
            sns_backend.platform_endpoint_messages.pop(saved_endpoint_arn, None)

        topic_arn = sns_create_topic()["TopicArn"]
        application_platform_name = f"app-platform-{short_uid()}"

        app_arn = sns_create_platform_application(
            Name=application_platform_name, Platform=platform, Attributes=attributes
        )["PlatformApplicationArn"]

        endpoint_arn = aws_client.sns.create_platform_endpoint(
            PlatformApplicationArn=app_arn, Token=short_uid()
        )["EndpointArn"]

        endpoint_arn_2 = aws_client.sns.create_platform_endpoint(
            PlatformApplicationArn=app_arn, Token=short_uid()
        )["EndpointArn"]

        sns_subscription(
            TopicArn=topic_arn,
            Protocol="application",
            Endpoint=endpoint_arn,
        )

        # example message from
        # https://docs.aws.amazon.com/sns/latest/dg/sns-send-custom-platform-specific-payloads-mobile-devices.html
        message = json.dumps({"APNS": json.dumps({"aps": {"content-available": 1}})})
        message_for_topic = {
            "default": "This is the default message which must be present when publishing a message to a topic.",
            "APNS": json.dumps({"aps": {"content-available": 1}}),
        }
        message_for_topic_string = json.dumps(message_for_topic)
        message_attributes = {
            "AWS.SNS.MOBILE.APNS.TOPIC": {
                "DataType": "String",
                "StringValue": "com.amazon.mobile.messaging.myapp",
            },
            "AWS.SNS.MOBILE.APNS.PUSH_TYPE": {
                "DataType": "String",
                "StringValue": "background",
            },
            "AWS.SNS.MOBILE.APNS.PRIORITY": {
                "DataType": "String",
                "StringValue": "5",
            },
        }
        # publish to a topic which has a platform subscribed to it
        aws_client.sns.publish(
            TopicArn=topic_arn,
            Message=message_for_topic_string,
            MessageAttributes=message_attributes,
            MessageStructure="json",
        )
        # publish directly to the platform endpoint
        aws_client.sns.publish(
            TargetArn=endpoint_arn_2,
            Message=message,
            MessageAttributes=message_attributes,
            MessageStructure="json",
        )

        # assert that message has been received
        def check_message():
            assert len(sns_backend.platform_endpoint_messages[endpoint_arn]) > 0

        retry(check_message, retries=PUBLICATION_RETRIES, sleep=PUBLICATION_TIMEOUT)

        msgs_url = config.internal_service_url() + PLATFORM_ENDPOINT_MSGS_ENDPOINT
        api_contents = requests.get(
            msgs_url, params={"region": region_name, "accountId": account_id}
        ).json()
        api_platform_endpoints_msgs = api_contents["platform_endpoint_messages"]

        assert len(api_platform_endpoints_msgs) == 2
        assert len(api_platform_endpoints_msgs[endpoint_arn]) == 1
        assert len(api_platform_endpoints_msgs[endpoint_arn_2]) == 1
        assert api_contents["region"] == region_name

        assert api_platform_endpoints_msgs[endpoint_arn][0]["Message"] == json.dumps(
            message_for_topic["APNS"]
        )
        assert (
            api_platform_endpoints_msgs[endpoint_arn][0]["MessageAttributes"] == message_attributes
        )

        # Ensure you can select the region
        msg_with_region = requests.get(
            msgs_url,
            params={"region": secondary_region_name, "accountId": account_id},
        ).json()
        assert len(msg_with_region["platform_endpoint_messages"]) == 0
        assert msg_with_region["region"] == secondary_region_name

        # Ensure default region is us-east-1
        msg_with_region = requests.get(msgs_url).json()
        assert msg_with_region["region"] == AWS_REGION_US_EAST_1

        # Ensure messages can be filtered by EndpointArn
        api_contents_with_endpoint = requests.get(
            msgs_url,
            params={
                "endpointArn": endpoint_arn,
                "region": region_name,
                "accountId": account_id,
            },
        ).json()
        msgs_with_endpoint = api_contents_with_endpoint["platform_endpoint_messages"]
        assert len(msgs_with_endpoint) == 1
        assert len(msgs_with_endpoint[endpoint_arn]) == 1
        assert api_contents_with_endpoint["region"] == region_name

        # Ensure you can reset the saved messages by EndpointArn
        delete_res = requests.delete(
            msgs_url,
            params={
                "endpointArn": endpoint_arn,
                "region": region_name,
                "accountId": account_id,
            },
        )
        assert delete_res.status_code == 204
        api_contents_with_endpoint = requests.get(
            msgs_url,
            params={
                "endpointArn": endpoint_arn,
                "region": region_name,
                "accountId": account_id,
            },
        ).json()
        msgs_with_endpoint = api_contents_with_endpoint["platform_endpoint_messages"]
        assert len(msgs_with_endpoint[endpoint_arn]) == 0

        # Ensure you can reset the saved messages by region
        delete_res = requests.delete(
            msgs_url, params={"region": region_name, "accountId": account_id}
        )
        assert delete_res.status_code == 204
        msg_with_region = requests.get(
            msgs_url, params={"region": region_name, "accountId": account_id}
        ).json()
        assert not msg_with_region["platform_endpoint_messages"]