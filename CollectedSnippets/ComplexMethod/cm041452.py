def test_publish_sms_can_retrospect(
        self,
        sns_create_topic,
        sns_subscription,
        aws_client,
        account_id,
        region_name,
        secondary_region_name,
    ):
        sns_store = SnsProvider.get_store(account_id, region_name)

        list_of_contacts = [
            f"+{random.randint(100000000, 9999999999)}",
            f"+{random.randint(100000000, 9999999999)}",
            f"+{random.randint(100000000, 9999999999)}",
        ]
        phone_number_1 = list_of_contacts[0]
        message = "Good news everyone!"
        topic_arn = sns_create_topic()["TopicArn"]
        for number in list_of_contacts:
            sns_subscription(TopicArn=topic_arn, Protocol="sms", Endpoint=number)

        # clean up the saved messages
        sns_store.sms_messages.clear()

        # publish to a topic which has a PhoneNumbers subscribed to it
        aws_client.sns.publish(Message=message, TopicArn=topic_arn)

        # publish directly to the PhoneNumber
        aws_client.sns.publish(
            PhoneNumber=phone_number_1,
            Message=message,
        )

        # assert that message has been received
        def check_message():
            assert len(sns_store.sms_messages) == 4

        retry(check_message, retries=PUBLICATION_RETRIES, sleep=PUBLICATION_TIMEOUT)

        msgs_url = config.internal_service_url() + SMS_MSGS_ENDPOINT
        api_contents = requests.get(
            msgs_url, params={"region": region_name, "accountId": account_id}
        ).json()
        api_sms_msgs = api_contents["sms_messages"]

        assert len(api_sms_msgs) == 3
        assert len(api_sms_msgs[phone_number_1]) == 2
        assert len(api_sms_msgs[list_of_contacts[1]]) == 1
        assert len(api_sms_msgs[list_of_contacts[2]]) == 1

        assert api_contents["region"] == region_name

        assert api_sms_msgs[phone_number_1][0]["Message"] == "Good news everyone!"

        # Ensure you can select the region
        msg_with_region = requests.get(msgs_url, params={"region": secondary_region_name}).json()
        assert len(msg_with_region["sms_messages"]) == 0
        assert msg_with_region["region"] == secondary_region_name

        # Ensure default region is us-east-1
        msg_with_region = requests.get(msgs_url).json()
        assert msg_with_region["region"] == AWS_REGION_US_EAST_1

        # Ensure messages can be filtered by EndpointArn
        api_contents_with_number = requests.get(
            msgs_url,
            params={
                "phoneNumber": phone_number_1,
                "accountId": account_id,
                "region": region_name,
            },
        ).json()
        msgs_with_number = api_contents_with_number["sms_messages"]
        assert len(msgs_with_number) == 1
        assert len(msgs_with_number[phone_number_1]) == 2
        assert api_contents_with_number["region"] == region_name

        # Ensure you can reset the saved messages by EndpointArn
        delete_res = requests.delete(
            msgs_url,
            params={
                "phoneNumber": phone_number_1,
                "accountId": account_id,
                "region": region_name,
            },
        )
        assert delete_res.status_code == 204
        api_contents_with_number = requests.get(
            msgs_url, params={"phoneNumber": phone_number_1}
        ).json()
        msgs_with_number = api_contents_with_number["sms_messages"]
        assert len(msgs_with_number[phone_number_1]) == 0

        # Ensure you can reset the saved messages by region
        delete_res = requests.delete(
            msgs_url, params={"region": region_name, "accountId": account_id}
        )
        assert delete_res.status_code == 204
        msg_with_region = requests.get(msgs_url, params={"region": region_name}).json()
        assert not msg_with_region["sms_messages"]