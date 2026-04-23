def test_send_email_can_retrospect(self, aws_client):
        # Test that sent emails can be retrospected through saved file and API access

        # reset endpoint stored messages
        EMAILS.clear()

        def _read_message_from_filesystem(message_id: str) -> dict:
            """Given a message ID, read the message from filesystem and deserialise it."""
            data_dir = config.dirs.data or config.dirs.tmp
            with open(os.path.join(data_dir, "ses", message_id + ".json")) as f:
                message = f.read()
            return json.loads(message)

        email = f"user-{short_uid()}@example.com"
        aws_client.ses.verify_email_address(EmailAddress=email)

        # Send a regular message
        message1 = aws_client.ses.send_email(
            Source=email,
            Message=SAMPLE_SIMPLE_EMAIL,
            Destination={
                "ToAddresses": ["success@example.com"],
            },
        )
        message1_id = message1["MessageId"]

        # Ensure saved message
        contents1 = _read_message_from_filesystem(message1_id)
        assert contents1["Id"] == message1_id
        assert contents1["Timestamp"]
        assert contents1["Region"]
        assert contents1["Source"] == email
        assert contents1["Destination"] == {"ToAddresses": ["success@example.com"]}
        assert contents1["Subject"] == SAMPLE_SIMPLE_EMAIL["Subject"]["Data"]
        assert contents1["Body"] == {
            "text_part": SAMPLE_SIMPLE_EMAIL["Body"]["Text"]["Data"],
            "html_part": SAMPLE_SIMPLE_EMAIL["Body"]["Html"]["Data"],
        }
        assert "RawData" not in contents1

        # Send a raw message
        raw_message_data = f"From: {email}\nTo: recipient@example.com\nSubject: test\n\nThis is the message body.\n\n"
        message2 = aws_client.ses.send_raw_email(RawMessage={"Data": raw_message_data})
        message2_id = message2["MessageId"]

        # Ensure saved raw message
        contents2 = _read_message_from_filesystem(message2_id)
        assert contents2["Id"] == message2_id
        assert contents2["Timestamp"]
        assert contents2["Region"]
        assert contents2["Source"] == email
        assert contents2["RawData"] == raw_message_data
        assert "Destination" not in contents2
        assert "Subject" not in contents2
        assert "Body" not in contents2

        # Ensure all sent messages can be retrieved using the API endpoint
        emails_url = config.internal_service_url() + EMAILS_ENDPOINT
        api_contents = []
        api_contents.extend(requests.get(emails_url + f"?id={message1_id}").json()["messages"])
        api_contents.extend(requests.get(emails_url + f"?id={message2_id}").json()["messages"])
        api_contents = {msg["Id"]: msg for msg in api_contents}
        assert len(api_contents) >= 1
        assert message1_id in api_contents
        assert message2_id in api_contents
        assert api_contents[message1_id] == contents1
        assert api_contents[message2_id] == contents2

        # Ensure messages can be filtered by email source via the REST endpoint
        emails_url = config.internal_service_url() + EMAILS_ENDPOINT + "?email=none@example.com"
        assert len(requests.get(emails_url).json()["messages"]) == 0
        emails_url = config.internal_service_url() + EMAILS_ENDPOINT + f"?email={email}"
        assert len(requests.get(emails_url).json()["messages"]) == 2

        emails_url = config.internal_service_url() + EMAILS_ENDPOINT
        assert requests.delete(emails_url + f"?id={message1_id}").status_code == 204
        assert requests.delete(emails_url + f"?id={message2_id}").status_code == 204
        assert requests.get(emails_url).json() == {"messages": []}