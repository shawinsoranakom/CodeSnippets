def test_subscribe_external_http_endpoint(
        self, sns_create_http_endpoint, raw_message_delivery, aws_client, snapshot
    ):
        def _get_snapshot_requests_response(response: requests.Response) -> dict:
            parsed_xml_body = xmltodict.parse(response.content)
            for root_tag, fields in parsed_xml_body.items():
                fields.pop("@xmlns", None)
                if "ResponseMetadata" in fields:
                    fields["ResponseMetadata"]["HTTPHeaders"] = dict(response.headers)
                    fields["ResponseMetadata"]["HTTPStatusCode"] = response.status_code
            return parsed_xml_body

        def _clean_headers(response_headers: dict):
            return {key: val for key, val in response_headers.items() if "Forwarded" not in key}

        snapshot.add_transformer(
            [
                snapshot.transform.key_value("RequestId"),
                snapshot.transform.key_value("Token"),
                snapshot.transform.key_value("Host"),
                snapshot.transform.key_value(
                    "Content-Length", reference_replacement=False
                ),  # might change depending on compression
                snapshot.transform.key_value(
                    "Connection", reference_replacement=False
                ),  # casing might change
                snapshot.transform.regex(
                    r"(?i)(?<=SubscribeURL[\"|']:\s[\"|'])(https?.*?)(?=/\?Action=ConfirmSubscription)",
                    replacement="<subscribe-domain>",
                ),
            ]
        )

        # Necessitate manual set up to allow external access to endpoint, only in local testing
        topic_arn, subscription_arn, endpoint_url, server = sns_create_http_endpoint(
            raw_message_delivery
        )
        assert poll_condition(
            lambda: len(server.log) >= 1,
            timeout=5,
        )
        sub_request, _ = server.log[0]
        payload = sub_request.get_json(force=True)
        snapshot.match("subscription-confirmation", payload)
        assert payload["Type"] == "SubscriptionConfirmation"
        assert sub_request.headers["x-amz-sns-message-type"] == "SubscriptionConfirmation"
        assert "Signature" in payload
        assert "SigningCertURL" in payload

        snapshot.match("http-confirm-sub-headers", _clean_headers(sub_request.headers))

        token = payload["Token"]
        subscribe_url = payload["SubscribeURL"]
        service_url, subscribe_url_path = payload["SubscribeURL"].rsplit("/", maxsplit=1)
        assert subscribe_url == (
            f"{service_url}/?Action=ConfirmSubscription&TopicArn={topic_arn}&Token={token}"
        )

        test_broken_confirm_url = (
            f"{service_url}/?Action=ConfirmSubscription&TopicArn=not-an-arn&Token={token}"
        )
        broken_confirm_subscribe_request = requests.get(test_broken_confirm_url)
        snapshot.match(
            "broken-topic-arn-confirm",
            _get_snapshot_requests_response(broken_confirm_subscribe_request),
        )

        test_broken_token_confirm_url = (
            f"{service_url}/?Action=ConfirmSubscription&TopicArn={topic_arn}&Token=abc123"
        )
        broken_token_confirm_subscribe_request = requests.get(test_broken_token_confirm_url)
        snapshot.match(
            "broken-token-confirm",
            _get_snapshot_requests_response(broken_token_confirm_subscribe_request),
        )

        # using the right topic name with a different region will fail when confirming the subscription
        parsed_arn = parse_arn(topic_arn)
        different_region = "eu-central-1" if parsed_arn["region"] != "eu-central-1" else "us-east-1"
        different_region_topic = topic_arn.replace(parsed_arn["region"], different_region)
        different_region_topic_confirm_url = f"{service_url}/?Action=ConfirmSubscription&TopicArn={different_region_topic}&Token={token}"
        region_topic_confirm_subscribe_request = requests.get(different_region_topic_confirm_url)
        snapshot.match(
            "different-region-arn-confirm",
            _get_snapshot_requests_response(region_topic_confirm_subscribe_request),
        )

        # but a nonexistent topic in the right region will succeed
        last_fake_topic_char = "a" if topic_arn[-1] != "a" else "b"
        nonexistent = topic_arn[:-1] + last_fake_topic_char
        assert nonexistent != topic_arn
        test_wrong_topic_confirm_url = (
            f"{service_url}/?Action=ConfirmSubscription&TopicArn={nonexistent}&Token={token}"
        )
        wrong_topic_confirm_subscribe_request = requests.get(test_wrong_topic_confirm_url)
        snapshot.match(
            "nonexistent-token-confirm",
            _get_snapshot_requests_response(wrong_topic_confirm_subscribe_request),
        )

        # weirdly, even with a wrong topic, SNS will confirm the topic
        subscription_attributes = aws_client.sns.get_subscription_attributes(
            SubscriptionArn=subscription_arn
        )
        assert subscription_attributes["Attributes"]["PendingConfirmation"] == "false"

        confirm_subscribe_request = requests.get(subscribe_url)
        confirm_subscribe = xmltodict.parse(confirm_subscribe_request.content)
        assert (
            confirm_subscribe["ConfirmSubscriptionResponse"]["ConfirmSubscriptionResult"][
                "SubscriptionArn"
            ]
            == subscription_arn
        )
        # also confirm that ConfirmSubscription is idempotent
        snapshot.match(
            "confirm-subscribe", _get_snapshot_requests_response(confirm_subscribe_request)
        )

        subscription_attributes = aws_client.sns.get_subscription_attributes(
            SubscriptionArn=subscription_arn
        )
        assert subscription_attributes["Attributes"]["PendingConfirmation"] == "false"

        message = "test_external_http_endpoint"
        aws_client.sns.publish(TopicArn=topic_arn, Message=message)

        assert poll_condition(
            lambda: len(server.log) >= 2,
            timeout=5,
        )
        notification_request, _ = server.log[1]
        assert notification_request.headers["x-amz-sns-message-type"] == "Notification"

        expected_unsubscribe_url = (
            f"{service_url}/?Action=Unsubscribe&SubscriptionArn={subscription_arn}"
        )
        if raw_message_delivery:
            payload = notification_request.data.decode()
            assert payload == message
            snapshot.match("http-message-headers-raw", _clean_headers(notification_request.headers))
        else:
            payload = notification_request.get_json(force=True)
            assert payload["Type"] == "Notification"
            assert "Signature" in payload
            assert "SigningCertURL" in payload
            assert payload["Message"] == message
            assert payload["UnsubscribeURL"] == expected_unsubscribe_url
            snapshot.match("http-message", payload)
            snapshot.match("http-message-headers", _clean_headers(notification_request.headers))

        unsub_request = requests.get(expected_unsubscribe_url)
        unsubscribe_confirmation = xmltodict.parse(unsub_request.content)
        assert "UnsubscribeResponse" in unsubscribe_confirmation
        snapshot.match("unsubscribe-response", _get_snapshot_requests_response(unsub_request))

        assert poll_condition(
            lambda: len(server.log) >= 3,
            timeout=5,
        )
        unsub_request, _ = server.log[2]

        payload = unsub_request.get_json(force=True)
        assert payload["Type"] == "UnsubscribeConfirmation"
        assert unsub_request.headers["x-amz-sns-message-type"] == "UnsubscribeConfirmation"
        assert "Signature" in payload
        assert "SigningCertURL" in payload
        token = payload["Token"]
        assert payload["SubscribeURL"] == (
            f"{service_url}/?Action=ConfirmSubscription&TopicArn={topic_arn}&Token={token}"
        )
        snapshot.match("unsubscribe-request", payload)