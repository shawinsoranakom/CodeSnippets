def test_ses_sns_topic_integration_send_email_ses_destination(
        self,
        sns_topic,
        sns_subscription,
        ses_configuration_set,
        ses_configuration_set_sns_event_destination,
        setup_email_addresses,
        aws_client,
    ):
        """
        Validates that configure Event Destinations and sending an email does not trigger an infinite loop of sending
        SNS notifications that sends an email that would trigger SNS.
        """

        sender_email_address, recipient_email_address = setup_email_addresses()
        config_set_name = f"config-set-{short_uid()}"

        emails_url = config.internal_service_url() + EMAILS_ENDPOINT
        response = requests.delete(emails_url)
        assert response.status_code == 204

        # create subscription to get notified about SES events
        topic_arn = sns_topic["Attributes"]["TopicArn"]
        sns_subscription(
            TopicArn=topic_arn,
            Protocol="email",
            Endpoint=sender_email_address,
        )

        # create the config set
        ses_configuration_set(config_set_name)
        event_destination_name = f"config-set-event-destination-{short_uid()}"
        ses_configuration_set_sns_event_destination(
            config_set_name, event_destination_name, topic_arn
        )

        # send an email to trigger the SNS message and SES message
        destination = {
            "ToAddresses": [recipient_email_address],
        }
        send_email = aws_client.ses.send_email(
            Destination=destination,
            Message=SAMPLE_SIMPLE_EMAIL,
            ConfigurationSetName=config_set_name,
            Source=sender_email_address,
            Tags=[
                {
                    "Name": "custom-tag",
                    "Value": "tag-value",
                }
            ],
        )

        def _get_emails():
            _resp = requests.get(emails_url)
            return _resp.json()["messages"]

        poll_condition(lambda: len(_get_emails()) >= 4, timeout=3)
        requests.delete(emails_url, params={"id": send_email["MessageId"]})

        emails = _get_emails()
        # we assert that we only received 3 emails
        assert len(emails) == 3

        emails = sorted(emails, key=lambda x: x["Body"]["text_part"])
        # the first email is the validation of SNS confirming the SES subscription
        ses_delivery_notification = emails[1]
        ses_send_notification = emails[2]

        assert ses_delivery_notification["Subject"] == "SNS-Subscriber-Endpoint"
        delivery_payload = json.loads(ses_delivery_notification["Body"]["text_part"])
        assert delivery_payload["eventType"] == "Delivery"
        assert delivery_payload["mail"]["source"] == sender_email_address

        assert ses_send_notification["Subject"] == "SNS-Subscriber-Endpoint"
        send_payload = json.loads(ses_send_notification["Body"]["text_part"])
        assert send_payload["eventType"] == "Send"
        assert send_payload["mail"]["source"] == sender_email_address