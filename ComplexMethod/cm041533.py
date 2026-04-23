def test_external_host_via_header_complete_message_lifecycle(
        self, monkeypatch, account_id, region_name
    ):
        monkeypatch.setattr(config, "SQS_ENDPOINT_STRATEGY", "off")

        queue_name = f"queue-{short_uid()}"

        edge_url = config.internal_service_url()
        headers = mock_aws_request_headers(
            "sqs",
            aws_access_key_id=TEST_AWS_ACCESS_KEY_ID,
            region_name=region_name,
        )
        port = 12345
        hostname = "aws-local"

        url = f"{hostname}:{port}"
        payload = f"Action=CreateQueue&QueueName={queue_name}"
        result = requests.post(edge_url, data=payload, headers=headers)
        assert result.status_code == 200

        queue_url = f"http://{url}/{account_id}/{queue_name}"
        message_body = f"test message {short_uid()}"
        payload = f"Action=SendMessage&QueueUrl={queue_url}&MessageBody={message_body}"
        result = requests.post(edge_url, data=payload, headers=headers)
        assert result.status_code == 200
        assert "MD5" in result.text

        payload = f"Action=ReceiveMessage&QueueUrl={queue_url}&VisibilityTimeout=0"
        result = requests.post(edge_url, data=payload, headers=headers)
        assert result.status_code == 200
        assert message_body in result.text

        # the customer said that he used to be able to access it via "127.0.0.1" instead of "aws-local" as well
        queue_url = f"http://127.0.0.1/{account_id}/{queue_name}"

        payload = f"Action=SendMessage&QueueUrl={queue_url}&MessageBody={message_body}"
        result = requests.post(edge_url, data=payload, headers=headers)
        assert result.status_code == 200
        assert "MD5" in result.text

        queue_url = f"http://127.0.0.1/{account_id}/{queue_name}"

        payload = f"Action=ReceiveMessage&QueueUrl={queue_url}&VisibilityTimeout=0"
        result = requests.post(edge_url, data=payload, headers=headers)
        assert result.status_code == 200
        assert message_body in result.text