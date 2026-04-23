def test_send_templated_email_can_retrospect(self, create_template, aws_client):
        # Test that sent emails can be retrospected through saved file and API access

        # reset endpoint stored messages
        EMAILS.clear()

        data_dir = config.dirs.data or config.dirs.tmp
        email = f"user-{short_uid()}@example.com"
        aws_client.ses.verify_email_address(EmailAddress=email)
        aws_client.ses.delete_template(TemplateName=SAMPLE_TEMPLATE["TemplateName"])
        create_template(template=SAMPLE_TEMPLATE)

        message = aws_client.ses.send_templated_email(
            Source=email,
            Template=SAMPLE_TEMPLATE["TemplateName"],
            TemplateData='{"A key": "A value"}',
            Destination={
                "ToAddresses": ["success@example.com"],
            },
        )
        message_id = message["MessageId"]

        with open(os.path.join(data_dir, "ses", message_id + ".json")) as f:
            message = f.read()

        contents = json.loads(message)

        assert email == contents["Source"]
        assert SAMPLE_TEMPLATE["TemplateName"] == contents["Template"]
        assert '{"A key": "A value"}' == contents["TemplateData"]
        assert ["success@example.com"] == contents["Destination"]["ToAddresses"]

        api_contents = requests.get("http://localhost:4566/_aws/ses").json()
        api_contents = {msg["Id"]: msg for msg in api_contents["messages"]}
        assert message_id in api_contents
        assert api_contents[message_id] == contents

        assert requests.delete("http://localhost:4566/_aws/ses").status_code == 204
        assert requests.get("http://localhost:4566/_aws/ses").json() == {"messages": []}